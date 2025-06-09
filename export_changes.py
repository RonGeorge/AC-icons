import sqlite3
import json
import os

SOURCE_DB = os.path.join("source", "acicons_original.db")
USER_DB = "acicons.db"
PATCH_FILE = "patch.json"


def fetch_data(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT icon_id, name, keywords, metadata_json FROM ac_icons")
    data = cursor.fetchall()
    conn.close()
    return {row[0]: row[1:] for row in data}  # icon_id: (name, keywords, metadata_json)


def generate_patch():
    if not os.path.exists(SOURCE_DB):
        print(f"Error: Source DB not found at {SOURCE_DB}")
        return
    if not os.path.exists(USER_DB):
        print(f"Error: User DB not found at {USER_DB}")
        return

    original = fetch_data(SOURCE_DB)
    modified = fetch_data(USER_DB)

    patch = {}
    for icon_id, new_values in modified.items():
        if icon_id not in original:
            patch[icon_id] = {
                "action": "add",
                "name": new_values[0],
                "keywords": new_values[1],
                "metadata_json": new_values[2]
            }
        elif original[icon_id] != new_values:
            patch[icon_id] = {
                "action": "update",
                "name": new_values[0],
                "keywords": new_values[1],
                "metadata_json": new_values[2]
            }

    if patch:
        with open(PATCH_FILE, "w", encoding="utf-8") as f:
            json.dump(patch, f, indent=2)
        print(f"Patch file created: {PATCH_FILE} ({len(patch)} changes)")
    else:
        print("No changes detected. Patch not created.")


if __name__ == "__main__":
    generate_patch()
