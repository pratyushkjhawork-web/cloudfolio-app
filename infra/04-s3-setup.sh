#!/bin/bash
# ============================================================
# Step 4: S3
# Creates a bucket for storing generated PDFs/assets, with:
#   - Default encryption at rest (AES256 — the Sandbox's KMS is
#     list-only, so we can't use a customer-managed KMS key; this
#     is still real "encryption at rest", just AWS-managed keys)
#   - A lifecycle rule (delete objects after 30 days) — satisfies
#     the "S3 Lifecycle Policies" course topic
# ============================================================
set -e
source "$(dirname "$0")/00-variables.sh"

echo "--- Creating S3 bucket: $S3_BUCKET_NAME ---"
aws s3api create-bucket \
  --bucket "$S3_BUCKET_NAME" \
  --region "$AWS_REGION" 2>/dev/null || echo "(bucket may already exist, continuing)"

echo "--- Blocking public access (good practice, screenshot-worthy for security slide) ---"
aws s3api put-public-access-block \
  --bucket "$S3_BUCKET_NAME" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --region "$AWS_REGION"

echo "--- Enabling default encryption (AES256) ---"
aws s3api put-bucket-encryption \
  --bucket "$S3_BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }' \
  --region "$AWS_REGION"

echo "--- Adding lifecycle rule (delete objects after 30 days) ---"
aws s3api put-bucket-lifecycle-configuration \
  --bucket "$S3_BUCKET_NAME" \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "expire-old-pdfs",
      "Status": "Enabled",
      "Filter": {"Prefix": ""},
      "Expiration": {"Days": 30}
    }]
  }' \
  --region "$AWS_REGION"

echo "S3_BUCKET_NAME=$S3_BUCKET_NAME" >> "$(dirname "$0")/.infra-state"

echo ""
echo "=== Step 4 complete ==="
echo "Bucket: $S3_BUCKET_NAME"
echo ""
echo "Screenshot suggestion: AWS Console -> S3 -> this bucket -> Properties tab "
echo "(show encryption enabled) and Management tab (show the lifecycle rule)"
echo ""
echo "=== ALL INFRA SCRIPTS COMPLETE ==="
echo "Your app should be live at: http://\$(grep PUBLIC_IP .infra-state | cut -d= -f2):8000"
