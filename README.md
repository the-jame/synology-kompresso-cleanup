# Synology Kompresso Cleanup

Find and quarantine large original videos left behind after [Kompresso](https://kompresso.app/) creates a smaller replacement that Synology Photos uploads as a new file.

The script matches videos using preserved Apple `Keys:CreationDate` metadata, similar duration, and a minimum 50% size reduction. It does not rely on filenames, folder dates, or upload dates.

## Requirements

Run this on a Linux machine or VM with the Synology Photos directory mounted.

- Python 3
- ExifTool
- Read/write access to the mounted Synology directory

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y libimage-exiftool-perl
```

## Setup

Edit the configuration at the top of `syno_metadata_cleanup.py`:

```python
TARGET_DIR = "/mnt/synology/Photos/MobileBackup"

# Keep enabled for the first run.
DRY_RUN = True

# Keep this OUTSIDE the Photos directory.
QUARANTINE_DIR = "/mnt/synology/Kompresso_originals_quarantine"
```

Example mount layout:

```text
/mnt/synology/
├── Photos/
│   └── MobileBackup/
└── Kompresso_originals_quarantine/
```

> **Important:** Keep `QUARANTINE_DIR` outside the Synology `Photos` directory. Otherwise Synology Photos may index quarantined originals and continue showing them in the library.

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
  Original: /mnt/synology/Photos/MobileBackup/iPhone/2026/07/IMG_4353.MOV (291,444,571 bytes)
  Keep:     /mnt/synology/Photos/MobileBackup/iPhone/2026/07/5EFDB8BF_IMG_4353.mov (12,795,014 bytes)
  Saved:    278,649,557 bytes
  ACTION: would move original to quarantine
```

Review the output carefully.

When satisfied, change:

```python
DRY_RUN = True
```

to:

```python
DRY_RUN = False
```

Run the script again:

```bash
./syno_metadata_cleanup.py
```

Matching large originals are moved to the quarantine directory while the smaller Kompresso versions remain in place.

After confirming the smaller videos play correctly in Synology Photos, permanently remove quarantined originals:

```bash
rm -rf /mnt/synology/Kompresso_originals_quarantine
```

## Matching rules

A pair is matched only when:

- Both videos have the same Apple `Keys:CreationDate` metadata.
- Their durations are within `DURATION_TOLERANCE_SECONDS`.
- The smaller file is at least 50% smaller than the larger file.
- Exactly two videos share that creation timestamp.

Groups with more than two videos sharing a timestamp are reported as ambiguous and skipped.

## Notes

- Always start with `DRY_RUN = True`.
- Keep a backup before moving or deleting files.
- The script ignores Synology `@eaDir` metadata/cache directories.
- If Synology Photos shows a removed video as a `?` thumbnail, refresh/wait for indexing or delete the stale entry in Synology Photos.

## License

MIT
