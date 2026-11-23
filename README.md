# Restore Manifest

Offline cloud-operations learning lab. Compare restored files with a previously captured SHA-256 manifest. No AWS account or credentials are used. Initial code was AI-assisted.

## Run

Use Python 3.9 or later. This is a code compatibility target, not a claim that Dahoba tested every version.

```sh
python restore_manifest.py capture examples/source baseline.json
cp -R examples/source restored
python restore_manifest.py verify restored baseline.json
printf 'changed\n' >> restored/config.txt
python restore_manifest.py verify restored baseline.json
python -m unittest discover -s tests -v
```

The first verify should return 0. The second should return 1. Input errors return 2. Capture refuses to replace an existing baseline. Keep baseline.json outside the directory being captured. The CLI compares file bytes and sizes and lists missing, changed and unexpected files. It refuses symlinks and special files.

## What this does not prove

A matching hash inventory is not a successful application restore. It does not validate database consistency, permissions, ownership, timestamps, availability, RPO or RTO. It does not restore or download cloud backups. The manifest is not signed: if someone replaces both data and manifest, this tool cannot detect that. Store the baseline separately with appropriate access controls. File names may reveal sensitive information. Do not commit real manifests or data.

Run only against a stable offline directory you control, with untrusted writers stopped. Files can change during scanning; this is not a hardened hostile-filesystem scanner. Empty directories are not represented. Large datasets need separate performance testing.

## Study route

See GUIDE_AR.md. Before an interview, run the commands, change one file, delete another and explain why byte equality is weaker than application health. No claim is made that Dahoba has personally run or reviewed this lab.

Reference: AWS Backup distinguishes restore completion from application-specific validation: https://docs.aws.amazon.com/aws-backup/latest/devguide/restore-testing-validation.html
