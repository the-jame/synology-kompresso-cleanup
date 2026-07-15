#!/usr/bin/env python3
import json
import os
import subprocess
from collections import defaultdict

TARGET_DIR = "/your/synology/photos/directory"
# e.g.
# TARGET_DIR = "/mnt/synology/Photos/MobileBackup"

# True = report only. Nothing is changed.
DRY_RUN = False

# When above is False, originals are moved here, not permanently deleted.
QUARANTINE_DIR = "/your/quarantine/directory"
# e.g.
# QUARANTINE_DIR = "/mnt/synology/Kompresso_originals_quarantine"

# Extra safety: recordings must have nearly the same duration.
DURATION_TOLERANCE_SECONDS = 1.0

print("=== METADATA-BASED VIDEO DUPLICATE SCAN ===")
print(f"Scanning: {TARGET_DIR}")
print("Status: DRY RUN — no files will be changed")
print("Match key: Keys:CreationDate + near-identical duration")
print("Size rule: compressed file must be at least 50% smaller")
print()

cmd = [
    "exiftool",
    "-j",
    "-G1",
    "-n",
    "-r",
    "-ext", "mp4",
    "-ext", "mov",
    "-ext", "mkv",
    "-Keys:CreationDate",
    "-QuickTime:Duration",
    TARGET_DIR,
]

result = subprocess.run(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
    check=True,
)

records = []

for item in json.loads(result.stdout):
    path = item.get("SourceFile")
    creation_date = item.get("Keys:CreationDate")
    duration = item.get("QuickTime:Duration")

    if not path or "/@eaDir/" in path:
        continue

    # No preserved Apple CreationDate or no readable duration: skip it.
    if not creation_date or duration is None:
        continue

    try:
        size = os.path.getsize(path)
        duration = float(duration)
    except (OSError, ValueError, TypeError):
        continue

    records.append({
        "path": path,
        "creation_date": creation_date,
        "duration": duration,
        "size": size,
    })

# Group strictly by the preserved Apple creation timestamp.
by_date = defaultdict(list)
for record in records:
    by_date[record["creation_date"]].append(record)

matches = 0
ambiguous = 0

for creation_date in sorted(by_date):
    group = by_date[creation_date]

    # More than two files recorded in the same second: don't guess.
    if len(group) != 2:
        if len(group) > 1:
            ambiguous += 1
            print(f"[AMBIGUOUS — SKIPPED] {creation_date}")
            for video in group:
                print(
                    f"  {video['size']:,} bytes | "
                    f"{video['duration']:.2f}s | {video['path']}"
                )
            print()
        continue

    a, b = group

    # Same metadata date alone is strong, but duration is a useful second check.
    if abs(a["duration"] - b["duration"]) > DURATION_TOLERANCE_SECONDS:
        continue

    larger, smaller = sorted((a, b), key=lambda x: x["size"], reverse=True)

    # Smaller must be 50% or less of original size.
    if smaller["size"] * 2 > larger["size"]:
        continue

    saved = larger["size"] - smaller["size"]
    matches += 1

    print(f"[MATCH] Apple CreationDate: {creation_date}")
    print(f"  Duration: {larger['duration']:.2f}s / {smaller['duration']:.2f}s")
    print(f"  Original: {larger['path']} ({larger['size']:,} bytes)")
    print(f"  Keep:     {smaller['path']} ({smaller['size']:,} bytes)")
    print(f"  Saved:    {saved:,} bytes")

    if DRY_RUN:
        print("  ACTION: would move original to quarantine")
    else:
        relative_path = os.path.relpath(larger["path"], TARGET_DIR)
        quarantine_path = os.path.join(QUARANTINE_DIR, relative_path)

        os.makedirs(os.path.dirname(quarantine_path), exist_ok=True)

    if os.path.exists(quarantine_path):
        print(f"  ACTION: SKIPPED — already exists in quarantine: {quarantine_path}")
    else:
        print(f"  ACTION: moving original to: {quarantine_path}")
        os.rename(larger["path"], quarantine_path)

print()

print("------------------------------------------------")
print(f"Matches found: {matches}")
print(f"Ambiguous timestamp groups skipped: {ambiguous}")
