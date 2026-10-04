#!/bin/bash
# ============================================================
# Teardown — deletes everything these scripts created.
# The Sandbox wipes everything automatically when the session
# timer ends anyway, but run this if you want to clean up
# early (e.g. to stay well within the cost budget) or before
# re-running the full set from scratch.
# ============================================================
source "$(dirname "$0")/00-variables.sh"
source "$(dirname "$0")/.infra-state" 2>/dev/null || true

echo "--- Terminating EC2 instance ---"
[ -n "$INSTANCE_ID" ] && aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" || echo "(no instance recorded, skipping)"

echo "--- Deleting RDS instance (no final snapshot, this is a course project) ---"
aws rds delete-db-instance \
  --db-instance-identifier "$RDS_INSTANCE_ID" \
  --skip-final-snapshot \
  --region "$AWS_REGION" 2>/dev/null || echo "(no RDS instance found, skipping)"

echo "--- Emptying and deleting S3 bucket ---"
if [ -n "$S3_BUCKET_NAME" ]; then
  aws s3 rm "s3://$S3_BUCKET_NAME" --recursive --region "$AWS_REGION" 2>/dev/null || true
  aws s3api delete-bucket --bucket "$S3_BUCKET_NAME" --region "$AWS_REGION" 2>/dev/null || echo "(bucket already gone, skipping)"
fi

echo ""
echo "Note: security groups and the DB subnet group are left in place since"
echo "they're free and will vanish with the Sandbox session anyway. EC2 and"
echo "RDS were the only things actually costing credit."
echo ""
echo "Also deleting local state file so the next run starts clean:"
rm -f "$(dirname "$0")/.infra-state"
echo "Done."
