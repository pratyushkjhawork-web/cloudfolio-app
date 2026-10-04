#!/bin/bash
# ============================================================
# Shared config — SAFE TO COMMIT, contains no secrets.
# Real secrets (DB password, Gemini key) live in 00-secrets.sh,
# which is git-ignored and must be created fresh in the Sandbox
# IDE terminal each session — see 00-secrets.sh.example.
# ============================================================

export AWS_REGION="us-east-1"   # Sandbox only supports this region

# --- Your GitHub repo (must be public, so EC2 can clone it without auth) ---
export GITHUB_REPO_URL="https://github.com/pratyushkjhawork-web/cloudfolio-app.git"

export DB_NAME="cloudfolio"
export DB_USERNAME="cloudfolio_admin"

# --- Naming (safe to leave as-is) ---
export PROJECT_TAG="CloudFolio"
export SG_EC2_NAME="cloudfolio-ec2-sg"
export SG_RDS_NAME="cloudfolio-rds-sg"
export DB_SUBNET_GROUP_NAME="cloudfolio-db-subnet-group"
export RDS_INSTANCE_ID="cloudfolio-db"
export EC2_INSTANCE_NAME="cloudfolio-backend"
export S3_BUCKET_NAME="cloudfolio-resumes-$(aws sts get-caller-identity --query Account --output text 2>/dev/null)"

# Load the secrets file (DB_PASSWORD, GEMINI_API_KEY) — must exist, see 00-secrets.sh.example
SECRETS_FILE="$(dirname "$0")/00-secrets.sh"
if [ -f "$SECRETS_FILE" ]; then
  source "$SECRETS_FILE"
else
  echo "WARNING: 00-secrets.sh not found. Copy 00-secrets.sh.example to 00-secrets.sh"
  echo "and fill in your real DB password and Gemini key before running the other scripts."
fi

echo "Config loaded. Region: $AWS_REGION | S3 bucket will be: $S3_BUCKET_NAME"
