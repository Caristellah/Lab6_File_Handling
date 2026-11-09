import csv
import json
import os
import shutil
from collections import Counter

ID_SUM = 31
SEED_DIGIT = 2

RECORDS_TO_PROCESS = 1000 + 2
TARGET_CLASS = (2 % 4) + 2   # 2 -> 2xx, 3 -> 3xx, 4 -> 4xx, 5 -> 5xx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "weblog.csv")
FILTERED_CSV = os.path.join(BASE_DIR, "filtered_logs.csv")
SUMMARY_JSON = os.path.join(BASE_DIR, "log_summary.json")
BACKUP_JSON = os.path.join(BASE_DIR, "log_summary_backup.json")

def read_rows(path, limit):
    """Yield one row at a time, stopping after `limit` rows."""
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for count, row in enumerate(reader):
                if count >= limit:
                    break
                yield row
    except FileNotFoundError:
        raise SystemExit(f"File '{path}' not found.")

def extract_fields(row):
    """Return (ip, time, url, status) or None if the record is invalid."""
    try:
        status_raw = row.get("Staus", row.get("Status"))
        ip = row["IP"].strip()
        ts = row["Time"].strip()
        url = row["URL"].strip()
        status = int(status_raw.strip())
        if not ip or not ts or not url or not (100 <= status <= 599):
            return None
        return ip, ts, url, status
    except (KeyError, ValueError, TypeError, AttributeError):
        return None

processed = 0
invalid = 0
selected = []

for row in read_rows(INPUT_CSV, RECORDS_TO_PROCESS):
    processed += 1
    record = extract_fields(row)
    if record is None:
        invalid += 1
        continue
    ip, ts, url, status = record
    if status // 100 == TARGET_CLASS:
        selected.append({"IP": ip, "Time": ts, "URL": url, "Status": status})

status_counts = Counter(r["Status"] for r in selected)
url_counts = Counter(r["URL"] for r in selected)
top5 = url_counts.most_common(5)

with open(FILTERED_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["IP", "Time", "URL", "Status"])
    writer.writeheader()
    writer.writerows(selected)

summary = {
    "records_processed": processed,
    "invalid_records_skipped": invalid,
    "target_status_class": f"{TARGET_CLASS}xx",
    "records_in_target_class": len(selected),
    "count_per_status_code": {str(k): v for k, v in sorted(status_counts.items())},
    "five_most_requested_urls": [{"url": u, "count": c} for u, c in top5],
    "filtered_csv_file": os.path.basename(FILTERED_CSV),
}
with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=4)

backup_ok = False
try:
    shutil.copy2(SUMMARY_JSON, BACKUP_JSON)
    backup_ok = os.path.exists(BACKUP_JSON) and \
        os.path.getsize(BACKUP_JSON) == os.path.getsize(SUMMARY_JSON)
except OSError as e:
    print("Backup failed:", e)

print(f"Records processed        : {processed}")
print(f"Target status class      : {TARGET_CLASS}xx")
print(f"Records in target class  : {len(selected)}")
print(f"Count per status code    : {dict(sorted(status_counts.items()))}")
print("Five most requested URLs :")
for rank, (u, c) in enumerate(top5, 1):
    print(f"  {rank}. {u} ({c})")
print(f"Filtered CSV file        : {os.path.basename(FILTERED_CSV)}")
print(f"JSON summary file        : {os.path.basename(SUMMARY_JSON)}")
print(f"Backup verification     : {'PASSED' if backup_ok else 'FAILED'}")