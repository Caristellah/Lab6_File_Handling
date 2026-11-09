import csv
import json
import os
import shutil
from collections import Counter

SEED_DIGIT = 2

TARGET_YEAR = 2015 + 2 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "Global_Cybersecurity_Threats_2015-2024.csv")
FILTERED_CSV = os.path.join(BASE_DIR, "filtered_incidents.csv")
SUMMARY_JSON = os.path.join(BASE_DIR, "incident_summary.json")
BACKUP_JSON = os.path.join(BASE_DIR, "incident_summary_backup.json")
REPORT_TXT = os.path.join(BASE_DIR, "incident_report.txt")

YEAR_COL = "Year"
LOSS_COL = "Financial Loss (in Million $)"
TYPE_COL = "Attack Type"

total_records = 0
selected = []          
fieldnames = []

try:
    with open(INPUT_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            total_records += 1
            try:
                if int(float((row.get(YEAR_COL) or "").strip())) == TARGET_YEAR:
                    selected.append(row)
            except ValueError:
                continue         
except FileNotFoundError:
    raise SystemExit(f"File '{INPUT_CSV}' not found.")

if not selected:
    print(f"No incidents found for {TARGET_YEAR}.")

type_counts = Counter(
    (row.get(TYPE_COL) or "Unknown").strip() or "Unknown" for row in selected
)

valid_losses = []     
invalid_loss_count = 0

for index, row in enumerate(selected):
    try:
        loss = float((row.get(LOSS_COL) or "").strip())
        if loss < 0:
            raise ValueError("negative loss")
        valid_losses.append((index, loss, row))
    except ValueError:
        invalid_loss_count += 1

if valid_losses:
    total_loss = round(sum(item[1] for item in valid_losses), 2)
    average_loss = round(total_loss / len(valid_losses), 2)
else:
    total_loss = 0.0
    average_loss = None
    print("No valid financial loss values: average cannot be calculated.")

ranked = sorted(valid_losses, key=lambda item: item[1], reverse=True)
top5 = ranked[:5]
top5_records = [
    {"rank": rank, "financial_loss_million_usd": loss, "record": dict(row)}
    for rank, (index, loss, row) in enumerate(top5, 1)
]

TOP5_JSON = os.path.join(BASE_DIR, "top5_costliest_incidents.json")
with open(TOP5_JSON, "w", encoding="utf-8") as f:
    json.dump(top5_records, f, indent=4)

with open(FILTERED_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(selected)

summary = {
    "target_year": TARGET_YEAR,
    "total_records_in_dataset": total_records,
    "incidents_in_target_year": len(selected),
    "count_per_attack_type": dict(sorted(type_counts.items())),
    "invalid_loss_values_skipped": invalid_loss_count,
    "total_financial_loss_million_usd": total_loss,
    "average_financial_loss_million_usd": average_loss,
    "five_costliest_incidents": top5_records,
    "filtered_csv_file": os.path.basename(FILTERED_CSV),
}
with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=4)

backup_ok = False
try:
    shutil.copy2(SUMMARY_JSON, BACKUP_JSON)
    with open(SUMMARY_JSON, encoding="utf-8") as a, open(BACKUP_JSON, encoding="utf-8") as b:
        backup_ok = os.path.exists(BACKUP_JSON) and json.load(a) == json.load(b)
except (OSError, json.JSONDecodeError) as e:
    print("Backup failed:", e)

lines = []
lines.append("CYBERSECURITY INCIDENT REPORT")
lines.append("=" * 60)
lines.append(f"Target year               : {TARGET_YEAR}")
lines.append(f"Total records in dataset  : {total_records}")
lines.append(f"Incidents in target year  : {len(selected)}")
lines.append("")
lines.append("INCIDENT COUNT PER ATTACK TYPE")
lines.append("-" * 60)
for attack_type, count in sorted(type_counts.items()):
    lines.append(f"  {attack_type:<30} {count}")
lines.append("")
lines.append("FINANCIAL LOSSES (USD millions)")
lines.append("-" * 60)
lines.append(f"  Total loss               : {total_loss}")
lines.append(f"  Average loss             : {average_loss}")
lines.append(f"  Invalid values skipped   : {invalid_loss_count}")
lines.append("")
lines.append("FIVE COSTLIEST INCIDENTS")
lines.append("-" * 60)
if top5:
    for rank, (index, loss, row) in enumerate(top5, 1):
        lines.append(f"  {rank}. {(row.get(TYPE_COL) or '').strip()} | "
                     f"{(row.get('Country') or '').strip()} | "
                     f"{(row.get('Target Industry') or '').strip()} | "
                     f"${loss} million")
else:
    lines.append("  No incidents available.")
lines.append("")
lines.append("OUTPUT FILES")
lines.append("-" * 60)
for path in (FILTERED_CSV, SUMMARY_JSON, BACKUP_JSON, TOP5_JSON):
    lines.append(f"  {os.path.basename(path)}")
lines.append(f"  Backup verification      : {'PASSED' if backup_ok else 'FAILED'}")

with open(REPORT_TXT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Target year                    : {TARGET_YEAR}")
print(f"Total records in dataset       : {total_records}")
print(f"Incidents in target year       : {len(selected)}")
print(f"Count per attack type          : {dict(sorted(type_counts.items()))}")
print(f"Total financial loss (USD M)   : {total_loss}")
print(f"Average financial loss (USD M) : {average_loss}")
print("Five costliest incidents       :")
for rank, (index, loss, row) in enumerate(top5, 1):
    print(f"  {rank}. {(row.get(TYPE_COL) or '').strip()} - "
          f"{(row.get('Country') or '').strip()} - ${loss}M")
print(f"Filtered CSV file              : {os.path.basename(FILTERED_CSV)}")
print(f"JSON summary file              : {os.path.basename(SUMMARY_JSON)}")
print(f"Backup verification            : {'PASSED' if backup_ok else 'FAILED'}")
print(f"Report file                    : {os.path.basename(REPORT_TXT)}")