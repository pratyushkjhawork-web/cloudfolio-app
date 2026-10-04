#!/bin/bash
# ============================================================
# Shared config for all infra scripts.
# EDIT THE VALUES BELOW, then: source 00-variables.sh
# before running any other script in this folder (each script
# sources this automatically, but you must edit it first).
# ============================================================

export AWS_REGION="us-east-1"   # Sandbox only supports this region

# --- Your GitHub repo (must be public, or EC2 can't clone it without
# extra auth setup — easiest to make the repo public for the course) ---
export GITHUB_REPO_URL="https://github.com/pratyushkjhawork-web/cloudfolio-app.git"

# --- RDS MySQL credentials (pick your own password; 8+ chars, no quotes/@ symbols) ---
export DB_NAME="cloudfolio"
export DB_USERNAME="cloudfolio_admin"
export DB_PASSWORD="ChangeThisPassword123"   # <-- CHANGE THIS

# --- Gemini API key (for the AI features to work once deployed) ---
export GEMINI_API_KEY="your-gemini-key-here"   # <-- CHANGE THIS

# --- Naming (safe to leave as-is) ---
export PROJECT_TAG="CloudFolio"
export SG_EC2_NAME="cloudfolio-ec2-sg"
export SG_RDS_NAME="cloudfolio-rds-sg"
export DB_SUBNET_GROUP_NAME="cloudfolio-db-subnet-group"
export RDS_INSTANCE_ID="cloudfolio-db"
export EC2_INSTANCE_NAME="cloudfolio-backend"
export S3_BUCKET_NAME="cloudfolio-resumes-$(aws sts get-caller-identity --query Account --output text 2>/dev/null)"

echo "Config loaded. Region: $AWS_REGION | S3 bucket will be: $S3_BUCKET_NAME"
