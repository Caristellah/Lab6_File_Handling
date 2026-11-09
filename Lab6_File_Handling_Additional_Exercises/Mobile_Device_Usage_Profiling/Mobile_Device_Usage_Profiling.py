import csv
import json
import os
import shutil

SEED_DIGIT = 2

TARGET_OS = "Android" if 2 % 2 == 0 else "iOS"
TARGET_CLASS = (2 % 5) + 1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "user_behavior_dataset.csv")
EXPORT_CSV = os.path.join(BASE_DIR, "selected_users.csv")
SUMMARY_JSON = os.path.join(BASE_DIR, "usage_summary.json")
BACKUP_CSV = os.path.join(BASE_DIR, "selected_users_backup.csv")

EXPORT_FIELDS = ["User ID", "Device Model", "Operating System",
                 "Battery Drain (mAh/day)", "Data Usage (MB/day)"]

total_records = 0
os_matches = []

try:
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_records += 1
            if (row.get("Operating System") or "").strip().lower() == TARGET_OS.lower():
                os_matches.append(row)
except FileNotFoundError:
    raise SystemExit(f"File '{INPUT_CSV}' not found.")

selected = []
for row in os_matches:
    try:
        if int((row.get("User Behavior Class") or "").strip()) == TARGET_CLASS:
            selected.append(row)
    except ValueError:
        continue  

battery_values = []
data_values = []
for row in selected:
    try:
        battery_values.append(float(row["Battery Drain (mAh/day)"]))
        data_values.append(float(row["Data Usage (MB/day)"]))
    except (ValueError, KeyError, TypeError):
        continue    

if battery_values:
    avg_battery = round(sum(battery_values) / len(battery_values), 2)
    avg_data = round(sum(data_values) / len(data_values), 2)
else:
    avg_battery = None
    avg_data = None
    print("No matching records found: averages cannot be calculated.")

with open(EXPORT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(selected)

with open(EXPORT_CSV, newline="", encoding="utf-8") as f:
    exported_count = sum(1 for _ in csv.DictReader(f))
count_verified = (exported_count == len(selected))

summary = {
    "operating_system": TARGET_OS,
    "behavior_class": TARGET_CLASS,
    "total_records_in_dataset": total_records,
    "records_matching_os": len(os_matches),
    "records_in_target_class": len(selected),
    "average_battery_drain_mah_per_day": avg_battery,
    "average_data_usage_mb_per_day": avg_data,
    "selected_row_count": len(selected),
    "exported_row_count": exported_count,
    "count_verification": "MATCH" if count_verified else "MISMATCH",
    "exported_csv_file": os.path.basename(EXPORT_CSV),
}
with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=4)

backup_size = None
try:
    shutil.copy2(EXPORT_CSV, BACKUP_CSV)
    backup_size = os.path.getsize(BACKUP_CSV)
except OSError as e:
    print("Backup failed:", e)

print(f"Operating system and behavior class : {TARGET_OS}, Class {TARGET_CLASS}")
print(f"Total records in dataset            : {total_records}")
print(f"Records matching operating system   : {len(os_matches)}")
print(f"Records in target behavior class    : {len(selected)}")
print(f"Average battery drain (mAh/day)     : {avg_battery}")
print(f"Average data usage (MB/day)         : {avg_data}")
print(f"Count verification                  : {'MATCH' if count_verified else 'MISMATCH'} "
      f"(selected={len(selected)}, exported={exported_count})")
print(f"Exported CSV file                   : {os.path.basename(EXPORT_CSV)}")
print(f"JSON summary file                   : {os.path.basename(SUMMARY_JSON)}")
print(f"Backup file and size                : {os.path.basename(BACKUP_CSV)}, "
      f"{backup_size} bytes")