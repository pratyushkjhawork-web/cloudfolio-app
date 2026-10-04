# CloudFolio — AWS Deployment Scripts

Run these in the **AWS Academy Sandbox's VS Code IDE terminal** (not your
own machine — that terminal has AWS credentials pre-configured).

## Before you start

1. **Make your GitHub repo public** (or EC2's `git clone` in step 3 will fail).
2. Push your `backend/` and `frontend/` folders to it — `00-variables.sh`
   is safe to commit (no secrets in it).
3. In the Sandbox IDE terminal, create your secrets file (this file is
   git-ignored and NEVER gets pushed to GitHub — you recreate it each
   session since the Sandbox wipes its filesystem too):
   ```bash
   cp 00-secrets.sh.example 00-secrets.sh
   nano 00-secrets.sh   # or any editor — fill in DB_PASSWORD and GEMINI_API_KEY
   ```
4. If your GitHub repo URL changed, edit `GITHUB_REPO_URL` in `00-variables.sh`
   (this one IS committed, so only do this if the URL itself needs updating,
   not for secrets).

## Run order

```bash
chmod +x *.sh
source 00-variables.sh      # loads config + secrets (re-run if you open a new terminal)
./01-network-setup.sh       # VPC discovery + security groups  (~10 sec)
./02-rds-setup.sh           # RDS MySQL                        (~5-10 min, slow — be patient)
./03-ec2-launch.sh          # EC2 + auto-deploy via user-data   (~1-2 min + ~2 min app install)
./04-s3-setup.sh            # S3 bucket + encryption + lifecycle (~10 sec)
```

Each script prints what it did and a **screenshot suggestion** for your
final submission — take the screenshot right after that script finishes,
don't wait until the end (the Sandbox session will eventually expire).

After step 3, **wait ~2 minutes** for the app to finish installing on the
instance, then open the URL it prints (`http://<public-ip>:8000`).

If the app doesn't load after a few minutes, check what went wrong without
needing SSH:
```bash
aws ssm start-session --target <INSTANCE_ID> --region us-east-1
sudo cat /var/log/cloudfolio-userdata.log
```

## Re-running after a session reset

The Sandbox wipes everything when the session timer ends. Next time you
start a new session, just run the same 4 scripts again in order — the
`.infra-state` file from last time is harmless to leave around; each
script will just create fresh resources.

## Cleaning up early

```bash
./99-teardown.sh
```

Deletes the EC2 instance, RDS database, and S3 bucket — useful if you
want to free up credit before the session naturally expires, or before
re-running everything from a clean slate.

## What each script maps to in the course syllabus

| Script | AWS Services | Course Module |
|---|---|---|
| `01-network-setup.sh` | VPC, Security Groups | Module 2 — Networking |
| `02-rds-setup.sh` | RDS (MySQL) | Module 3 — Databases |
| `03-ec2-launch.sh` | EC2, IAM (LabInstanceProfile), SSM | Module 1, 4 — Compute, IAM |
| `04-s3-setup.sh` | S3 (encryption, lifecycle policy) | Module 1 — Storage |

## Known Sandbox-driven compromises (be ready to explain these in viva)

- **No custom VPC** — uses the Sandbox's default VPC. Custom VPC creation
  wasn't confirmed to work in this Sandbox; the security group
  segmentation (EC2 open to internet on 8000, RDS only reachable from
  EC2's security group) still demonstrates the access-control concept.
- **No Multi-AZ RDS** — explicitly unsupported by the Sandbox.
- **IAM via LabRole/LabInstanceProfile**, not custom least-privilege
  policies — the Sandbox's IAM is read-only for students.
- **No SQS** — wasn't in the Sandbox's service list, so the original
  async-PDF-via-queue design isn't implemented; PDF generation is
  synchronous instead.
- **KMS is AWS-managed (SSE-S3), not customer-managed** — Sandbox KMS
  access is list-only, no key creation.
