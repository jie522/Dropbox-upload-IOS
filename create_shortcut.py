#!/usr/bin/env python3
"""
生成 Dropbox 影片上傳 iOS 捷徑（.shortcut 檔案）

使用方式：
    python3 create_shortcut.py

輸出 DropboxVideoUpload.shortcut，可透過 AirDrop 或 Files app 匯入 iPhone。
"""

import plistlib
import uuid
import sys

FFFC = "\ufffc"  # Unicode Object Replacement Character（Shortcuts 變數佔位符）


def new_uuid():
    return str(uuid.uuid4()).upper()


# ── 序列化輔助函式 ──────────────────────────────────────────────────────────────

def plain_text(s):
    """純文字 WFTextTokenString（不含變數）。"""
    return {
        "WFSerializationType": "WFTextTokenString",
        "Value": {
            "string": s,
            "attachmentsByRange": {}
        }
    }


def text_with_vars(parts):
    """
    含變數的 WFTextTokenString。
    parts: list of str 或 (output_uuid, output_name) tuple。
    """
    combined = ""
    attachments = {}
    for part in parts:
        if isinstance(part, str):
            combined += part
        else:
            output_uuid, output_name = part
            pos = len(combined)
            combined += FFFC
            attachments[f"{{{pos}, 1}}"] = {
                "OutputName": output_name,
                "OutputUUID": output_uuid,
                "Type": "ActionOutput"
            }
    return {
        "WFSerializationType": "WFTextTokenString",
        "Value": {
            "string": combined,
            "attachmentsByRange": attachments
        }
    }


def var_ref(output_uuid, output_name):
    """單一變數引用（WFTextTokenAttachment）。"""
    return {
        "WFSerializationType": "WFTextTokenAttachment",
        "Value": {
            "OutputName": output_name,
            "OutputUUID": output_uuid,
            "Type": "ActionOutput"
        }
    }


def http_headers_dict(items):
    """
    建立 WFDictionaryFieldValue，用於 HTTP headers。
    items: list of (key_str, value_token) tuples。
    """
    return {
        "WFSerializationType": "WFDictionaryFieldValue",
        "Value": {
            "WFDictionaryFieldValueItems": [
                {
                    "WFItemType": 0,
                    "WFKey": plain_text(k),
                    "WFValue": v,
                }
                for k, v in items
            ]
        }
    }


# ── 捷徑動作建構 ──────────────────────────────────────────────────────────────

def build_shortcut(access_token, upload_folder):
    upload_folder = "/" + upload_folder.strip("/")

    # 每個動作的輸出 UUID
    SELECT_UUID   = new_uuid()
    REPEAT_UUID   = new_uuid()
    GROUP_UUID    = new_uuid()   # repeat 區塊用（start/end 共用）
    FMTDATE_UUID  = new_uuid()
    PATH_UUID     = new_uuid()
    APIARG_UUID   = new_uuid()

    actions = []

    # ── 1. Select Photos（影片、可多選）────────────────────────────────────────
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.selectphoto",
        "WFWorkflowActionParameters": {
            "UUID": SELECT_UUID,
            "CustomOutputName": "Photos",
            "WFPhotoMediaType": "Video",
            "SelectMultiple": True,
        }
    })

    # ── 2. Repeat with Each（開始）────────────────────────────────────────────
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "UUID": REPEAT_UUID,
            "GroupingIdentifier": GROUP_UUID,
            "WFControlFlowMode": 0,
            "WFInput": var_ref(SELECT_UUID, "Photos"),
        }
    })

    # ── 3. Format Date → 檔名時間戳記 ─────────────────────────────────────────
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.format.date",
        "WFWorkflowActionParameters": {
            "UUID": FMTDATE_UUID,
            "GroupingIdentifier": GROUP_UUID,
            "CustomOutputName": "Formatted Date",
            "WFDateFormatStyle": "Custom",
            "WFDateFormat": "yyyy-MM-dd_HH-mm-ss",
        }
    })

    # ── 4. Text：組成 Dropbox 路徑 ────────────────────────────────────────────
    # 結果例：/Videos/2024-01-15_14-30-00.MOV
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.text",
        "WFWorkflowActionParameters": {
            "UUID": PATH_UUID,
            "GroupingIdentifier": GROUP_UUID,
            "CustomOutputName": "DropboxPath",
            "WFTextActionText": text_with_vars([
                f"{upload_folder}/",
                (FMTDATE_UUID, "Formatted Date"),
                ".MOV",
            ]),
        }
    })

    # ── 5. Text：組成 Dropbox-API-Arg JSON ───────────────────────────────────
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.text",
        "WFWorkflowActionParameters": {
            "UUID": APIARG_UUID,
            "GroupingIdentifier": GROUP_UUID,
            "CustomOutputName": "APIArg",
            "WFTextActionText": text_with_vars([
                '{"path":"',
                (PATH_UUID, "DropboxPath"),
                '","mode":"add","autorename":true,"mute":false}',
            ]),
        }
    })

    # ── 6. Get Contents of URL（POST 上傳至 Dropbox）─────────────────────────
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "UUID": new_uuid(),
            "GroupingIdentifier": GROUP_UUID,
            "WFURL": plain_text("https://content.dropboxapi.com/2/files/upload"),
            "WFHTTPMethod": "POST",
            "WFHTTPBodyType": "File",
            "WFRequestVariable": var_ref(REPEAT_UUID, "Repeat Item"),
            "WFHTTPHeaders": http_headers_dict([
                ("Authorization",   plain_text(f"Bearer {access_token}")),
                ("Dropbox-API-Arg", text_with_vars([(APIARG_UUID, "APIArg")])),
                ("Content-Type",    plain_text("application/octet-stream")),
            ]),
        }
    })

    # ── 7. Repeat with Each（結束）────────────────────────────────────────────
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "UUID": new_uuid(),
            "GroupingIdentifier": GROUP_UUID,
            "WFControlFlowMode": 2,
        }
    })

    # ── 8. Show Notification ──────────────────────────────────────────────────
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "UUID": new_uuid(),
            "WFNotificationTitle": plain_text("上傳完成"),
            "WFNotificationActionBody": plain_text(
                f"影片已上傳至 Dropbox {upload_folder}/"
            ),
            "WFNotificationActionSound": True,
        }
    })

    return {
        "WFWorkflowActions": actions,
        "WFWorkflowClientVersion": "1239.0.1",
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowIcon": {
            "WFWorkflowIconGlyphNumber": 59745,      # cloud upload
            "WFWorkflowIconStartColor": 4278190335,  # blue
        },
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowName": "上傳影片到 Dropbox",
        "WFWorkflowNoInputBehavior": {
            "Name": "WFWorkflowNoInputBehaviorAskForInput",
            "Parameters": {}
        },
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowTypes": [],
    }


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  生成 Dropbox 影片上傳捷徑")
    print("=" * 60)
    print()
    print("尚未取得 Token？先執行：python3 get_dropbox_token.py")
    print()

    access_token = input("請輸入 Dropbox Access Token：").strip()
    if not access_token:
        print("錯誤：Access Token 不可為空。")
        sys.exit(1)

    folder = input("Dropbox 上傳目標資料夾（預設 /Videos，直接按 Enter 使用預設）：").strip()
    if not folder:
        folder = "/Videos"

    shortcut_data = build_shortcut(access_token, folder)

    output_path = "DropboxVideoUpload.shortcut"
    with open(output_path, "wb") as f:
        plistlib.dump(shortcut_data, f, fmt=plistlib.FMT_XML)

    print()
    print(f"已生成：{output_path}")
    print()
    print("匯入步驟：")
    print("  1. 將此檔案 AirDrop 到 iPhone")
    print("     或上傳到 iCloud Drive 後在 iPhone 的「檔案」app 中點開")
    print("  2. 在彈出視窗點選「加入捷徑」")
    print("  3. 開啟「捷徑」app，找到「上傳影片到 Dropbox」即可使用")
    print()
    print("注意：Access Token 已嵌入檔案，請勿將此 .shortcut 檔分享給他人。")


if __name__ == "__main__":
    main()
