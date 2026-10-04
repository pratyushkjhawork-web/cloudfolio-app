#!/bin/bash
# ============================================================
# Step 2: RDS MySQL
# Creates a DB subnet group (needs 2+ AZs even for a single-AZ
# instance — that's an RDS requirement, not a Multi-AZ setup)
# and launches a single-AZ db.t3.micro MySQL instance.
#
# Sandbox restriction: Multi-AZ is NOT supported — this script
# deliberately does NOT set --multi-az.
# ============================================================
set -e
source "$(dirname "$0")/00-variables.sh"
source "$(dirname "$0")/.infra-state"   # loads VPC_ID, ALL_SUBNET_IDS, RDS_SG_ID from step 1

echo "--- Creating DB subnet group across available AZs ---"
aws rds create-db-subnet-group \
  --db-subnet-group-name "$DB_SUBNET_GROUP_NAME" \
  --db-subnet-group-description "CloudFolio RDS subnet group" \
  --subnet-ids $ALL_SUBNET_IDS \
  --region "$AWS_REGION" 2>/dev/null || echo "(subnet group may already exist, continuing)"

echo "--- Launching RDS MySQL instance (this takes 5-10 minutes) ---"
aws rds create-db-instance \
  --db-instance-identifier "$RDS_INSTANCE_ID" \
  --db-name "$DB_NAME" \
  --engine mysql \
  --engine-version 8.0 \
  --db-instance-class db.t3.micro \
  --allocated-storage 20 \
  --storage-type gp2 \
  --master-username "$DB_USERNAME" \
  --master-user-password "$DB_PASSWORD" \
  --vpc-security-group-ids "$RDS_SG_ID" \
  --db-subnet-group-name "$DB_SUBNET_GROUP_NAME" \
  --no-multi-az \
  --no-publicly-accessible \
  --no-enable-performance-insights \
  --backup-retention-period 0 \
  --region "$AWS_REGION" 2>/dev/null || echo "(instance may already exist, continuing)"

echo "--- Waiting for RDS instance to become available (this is the slow part, be patient) ---"
aws rds wait db-instance-available \
  --db-instance-identifier "$RDS_INSTANCE_ID" \
  --region "$AWS_REGION"

echo "--- Fetching RDS endpoint ---"
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier "$RDS_INSTANCE_ID" \
  --query "DBInstances[0].Endpoint.Address" --output text --region "$AWS_REGION")

echo "RDS_ENDPOINT=$RDS_ENDPOINT" >> "$(dirname "$0")/.infra-state"

echo ""
echo "=== Step 2 complete ==="
echo "RDS Endpoint: $RDS_ENDPOINT"
echo ""
echo "Screenshot suggestion: AWS Console -> RDS -> Databases (show the instance: engine MySQL, "
echo "class db.t3.micro, Multi-AZ = No, status Available)"
echo "Next: run 03-ec2-launch.sh"
