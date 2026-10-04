#!/bin/bash
# ============================================================
# Step 1: Networking
# Discovers the Sandbox's default VPC/subnets (custom VPC
# creation isn't confirmed to work in this Sandbox, so we use
# the default VPC — still demonstrates VPC/Security Group
# concepts for the course, just not a hand-built custom VPC).
# Creates two security groups:
#   - cloudfolio-ec2-sg: allows inbound 8000 (the app) from
#     anywhere, so you/faculty can open it in a browser
#   - cloudfolio-rds-sg: allows inbound 3306 (MySQL) ONLY from
#     the EC2 security group — this is your least-privilege
#     story for the viva
# ============================================================
set -e  # stop immediately if any command fails
source "$(dirname "$0")/00-variables.sh"

echo "--- Confirming identity ---"
aws sts get-caller-identity

echo "--- Finding default VPC ---"
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=is-default,Values=true" \
  --query "Vpcs[0].VpcId" --output text --region "$AWS_REGION")
echo "Default VPC: $VPC_ID"

if [ "$VPC_ID" == "None" ]; then
  echo "ERROR: No default VPC found. You may need to create one manually in the console first."
  exit 1
fi

echo "--- Finding subnets in that VPC (need at least 2 AZs for RDS later) ---"
SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query "Subnets[].SubnetId" --output text --region "$AWS_REGION")
echo "Subnets found: $SUBNET_IDS"

# Save the first subnet for EC2, and all subnets for the RDS subnet group
SUBNET_ARRAY=($SUBNET_IDS)
EC2_SUBNET_ID=${SUBNET_ARRAY[0]}
echo "EC2_SUBNET_ID=$EC2_SUBNET_ID" > "$(dirname "$0")/.infra-state"
echo "VPC_ID=$VPC_ID" >> "$(dirname "$0")/.infra-state"
echo "ALL_SUBNET_IDS=\"$SUBNET_IDS\"" >> "$(dirname "$0")/.infra-state"

echo "--- Creating EC2 security group (allows inbound 8000 from anywhere) ---"
EC2_SG_ID=$(aws ec2 create-security-group \
  --group-name "$SG_EC2_NAME" \
  --description "CloudFolio EC2 - allows app traffic on 8000" \
  --vpc-id "$VPC_ID" \
  --query "GroupId" --output text --region "$AWS_REGION" 2>/dev/null || \
  aws ec2 describe-security-groups --filters "Name=group-name,Values=$SG_EC2_NAME" "Name=vpc-id,Values=$VPC_ID" \
  --query "SecurityGroups[0].GroupId" --output text --region "$AWS_REGION")
echo "EC2 Security Group: $EC2_SG_ID"

aws ec2 authorize-security-group-ingress \
  --group-id "$EC2_SG_ID" \
  --protocol tcp --port 8000 --cidr 0.0.0.0/0 \
  --region "$AWS_REGION" 2>/dev/null || echo "(rule may already exist, continuing)"

echo "--- Creating RDS security group (allows inbound 3306 ONLY from EC2 SG) ---"
RDS_SG_ID=$(aws ec2 create-security-group \
  --group-name "$SG_RDS_NAME" \
  --description "CloudFolio RDS - allows MySQL only from the EC2 security group" \
  --vpc-id "$VPC_ID" \
  --query "GroupId" --output text --region "$AWS_REGION" 2>/dev/null || \
  aws ec2 describe-security-groups --filters "Name=group-name,Values=$SG_RDS_NAME" "Name=vpc-id,Values=$VPC_ID" \
  --query "SecurityGroups[0].GroupId" --output text --region "$AWS_REGION")
echo "RDS Security Group: $RDS_SG_ID"

aws ec2 authorize-security-group-ingress \
  --group-id "$RDS_SG_ID" \
  --protocol tcp --port 3306 \
  --source-group "$EC2_SG_ID" \
  --region "$AWS_REGION" 2>/dev/null || echo "(rule may already exist, continuing)"

echo "EC2_SG_ID=$EC2_SG_ID" >> "$(dirname "$0")/.infra-state"
echo "RDS_SG_ID=$RDS_SG_ID" >> "$(dirname "$0")/.infra-state"

echo ""
echo "=== Step 1 complete ==="
echo "VPC:          $VPC_ID"
echo "EC2 Subnet:   $EC2_SUBNET_ID"
echo "EC2 SG:       $EC2_SG_ID (port 8000 open to internet)"
echo "RDS SG:       $RDS_SG_ID (port 3306 open ONLY to EC2 SG)"
echo ""
echo "Screenshot suggestion: AWS Console -> VPC -> Security Groups (show both groups and their rules)"
echo "Next: run 02-rds-setup.sh"
