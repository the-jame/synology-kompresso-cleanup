```markdown
# Synology Kompresso Cleanup

Safely identify large original videos that remain in Synology Photos after videos are recompressed with [Kompresso](https://kompresso.app/).

Kompresso creates a smaller re-encoded copy rather than destructively changing the original video. Synology Photos treats that replacement as a new upload, so both the large original and smaller compressed copy remain on the NAS.

This script finds high-confidence pairs using metadata preserved by Kompresso, then can move the larger originals to a quarantine folder for review.

## How it matches videos

A video pair is considered a match only when:

- Both files have the same Apple/QuickTime `Keys:CreationDate` metadata.
- Their durations are within 2 seconds of each other.
- One file is at least 50% smaller than the other.

The script does **not** rely on filenames, folder paths, upload dates, or filesystem modification times.

Any group with more than two videos sharing a creation timestamp is reported as **ambiguous** and skipped automatically.

## Requirements

Run the script from a Linux machine or VM that has the Synology Photos directory mounted.

Required packages:

- Python 3
- ExifTool
- Read/write access to the mounted Synology directory

Ubuntu/Debian installation:

```bash
sudo apt update
sudo apt install -y libimage-exiftool-perl
```

## Assumptions

This script assumes:

1. Your Synology Photos library is mounted on another machine.
2. The mounted location includes the `MobileBackup` directory.
3. Kompresso preserves Apple `Keys:CreationDate` metadata.
4. The compressed version is at least 50% smaller than the original.
5. You want to keep the compressed file and quarantine the larger original.
6. You have a backup before performing any cleanup.

Example mount layout:

```text
/mnt/synology/
└── Photos/
    └── MobileBackup/
        └── iPhone/
            ├── 2025/
            └── 2026/
```

## Configuration

Edit these variables at the top of `syno_metadata_cleanup.py`:

```python
TARGET_DIR = "/mnt/synology/Photos/MobileBackup"

# Keep this enabled until you have verified the output.
DRY_RUN = True

# IMPORTANT: Keep this outside the Photos directory.
QUARANTINE_DIR = "/mnt/synology/Kompresso_originals_quarantine"
```

`QUARANTINE_DIR` must be outside `Photos`. Anything inside the Synology Photos library may be indexed and continue appearing in Synology Photos.

## Usage

Make the script executable:

```bash
chmod +x syno_metadata_cleanup.py
```

Run a dry scan:

```bash
./syno_metadata_cleanup.py
```

Example output:

```text
[MATCH] Apple CreationDate: 2026:07:14 11:43:54-07:00
  Duration: 21.40s / 21.40s
  WOULD DELETE: /mnt/synology/Photos/MobileBackup/iPhone/2026/07/IMG_4353.MOV (291,444,571 bytes)
  WOULD KEEP:   /mnt/synology/Photos/MobileBackup/iPhone/2026/07/5EFDB8BF_IMG_4353.mov (12,795,014 bytes)
  Space saved:  278,649,557 bytes
```

Review every match carefully.

## Quarantine originals

After verifying the dry-run output, change:

```python
DRY_RUN = True
```

to:

```python
DRY_RUN = False
```

Then run the script again:

```bash
./syno_metadata_cleanup.py
```

The script moves matching large originals to:

```text
/mnt/synology/Kompresso_originals_quarantine/
```

It preserves the original directory structure within the quarantine directory.

For example:

```text
/mnt/synology/Kompresso_originals_quarantine/iPhone/2026/07/IMG_4353.MOV
```

The smaller Kompresso video remains in place.

## Synology Photos cleanup

After moving originals outside the `Photos` directory:

1. Wait for Synology Photos to notice the removed files.
2. Refresh Synology Photos.
3. If a removed original still appears as a `?` thumbnail, select that stale item in Synology Photos and delete it from the Photos interface.
4. Confirm the compressed video plays correctly.
5. Keep the quarantine folder until you are satisfied with the results.

When you are ready to permanently delete quarantined originals:

```bash
rm -rf /mnt/synology/Kompresso_originals_quarantine
```

This is irreversible.

## Safety notes

- Always start with `DRY_RUN = True`.
- Keep an independent backup before moving or deleting files.
- Do not place the quarantine directory inside Synology Photos.
- Ambiguous metadata groups are intentionally skipped.
- This script is designed for Kompresso-generated replacements and may not be appropriate for unrelated video libraries.
