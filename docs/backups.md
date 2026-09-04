# Backup and recovery

ApplyFlow 0.5 can create, verify, and restore validated local snapshots. These
commands never upload data or contact an external service.

## Create a backup

```bash
applyflow --data ~/private/applications.json backup \
  ~/private/backups/applyflow-2026-09-04.json \
  --json
```

The source must exist and pass the full store-schema validation. The destination
must be different from the source and must not already exist. ApplyFlow writes
the snapshot atomically, then reports its application count and SHA-256 digest.

Store the reported digest separately if you want to detect later changes.

## Verify a backup

Validate the schema and calculate the current checksum:

```bash
applyflow verify-backup ~/private/backups/applyflow-2026-09-04.json
```

Compare it with a previously recorded digest:

```bash
applyflow verify-backup ~/private/backups/applyflow-2026-09-04.json \
  --sha256 EXPECTED_64_CHARACTER_DIGEST \
  --json
```

A malformed store, unsupported schema, invalid expected digest, or checksum
mismatch returns status 2. Verification does not modify the backup.

## Restore safely

Restores always target a new path and require explicit confirmation:

```bash
applyflow restore ~/private/backups/applyflow-2026-09-04.json \
  --output ~/private/recovered/applications.json \
  --confirm
```

ApplyFlow validates the backup before writing. It refuses to overwrite an
existing output, including the active store. Review the restored file before
choosing whether to use it as your active `--data` store.

## Security boundaries

A checksum detects changes; it does not encrypt or authenticate a backup.
Anyone who can read the snapshot can read its company names, roles, URLs,
dates, and notes. Protect both active stores and backups with operating-system
permissions, disk encryption, and private storage.

Command output contains only the backup filename, application count, operation,
and SHA-256 digest. Parent directory names and application contents are omitted.
