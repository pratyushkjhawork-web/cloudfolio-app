#!/bin/bash
# ============================================================
# Step 3: EC2 launch
# Launches a t3.micro Amazon Linux instance with LabInstanceProfile
# attached (so SSM Session Manager works for shell access, no SSH
# key needed), and a user-data script that automatically:
#   1. Installs Python, git
#   2. Clones your GitHub repo
#   3. Writes a .env file with the RDS connection string + Gemini key
#   4. Installs dependencies and starts the app on port 8000
#
# This means every time the Sandbox resets, re-running 01, 02, 03
# rebuilds the whole thing from scratch automatically — no manual
# SSH-in-and-type-commands needed.
# ============================================================
set -e
source "$(dirname "$0")/00-variables.sh"
source "$(dirname "$0")/.infra-state"   # loads EC2_SUBNET_ID, EC2_SG_ID, RDS_ENDPOINT

if [ -z "$RDS_ENDPOINT" ]; then
  echo "ERROR: RDS_ENDPOINT not found — did you run 02-rds-setup.sh first?"
  exit 1
fi

echo "--- Finding latest Amazon Linux 2023 AMI ---"
AMI_ID=$(aws ssm get-parameters \
  --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query "Parameters[0].Value" --output text --region "$AWS_REGION")
echo "AMI: $AMI_ID"

echo "--- Building user-data (auto-deploy script run on first boot) ---"
cat > /tmp/user-data.sh << USERDATA
#!/bin/bash
exec > /var/log/cloudfolio-userdata.log 2>&1
echo "=== CloudFolio deployment starting \$(date) ==="

dnf install -y python3 python3-pip git

cd /home/ec2-user
git clone "$GITHUB_REPO_URL" cloudfolio-app
cd cloudfolio-app/backend

cat > .env << ENVFILE
DATABASE_URL=mysql+pymysql://$DB_USERNAME:$DB_PASSWORD@$RDS_ENDPOINT:3306/$DB_NAME
GEMINI_API_KEY=$GEMINI_API_KEY
ENVFILE

pip3 install -r requirements.txt

# Run the app as a background service so it survives the deploy
# script exiting, and restarts if it crashes.
cat > /etc/systemd/system/cloudfolio.service << SERVICE
[Unit]
Description=CloudFolio FastAPI app
After=network.target

[Service]
WorkingDirectory=/home/ec2-user/cloudfolio-app/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
User=ec2-user

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable cloudfolio
systemctl start cloudfolio

echo "=== CloudFolio deployment finished \$(date) ==="
USERDATA

echo "--- Launching EC2 instance ---"
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --subnet-id "$EC2_SUBNET_ID" \
  --security-group-ids "$EC2_SG_ID" \
  --iam-instance-profile Name=LabInstanceProfile \
  --user-data file:///tmp/user-data.sh \
  --associate-public-ip-address \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$EC2_INSTANCE_NAME},{Key=Project,Value=$PROJECT_TAG}]" \
  --query "Instances[0].InstanceId" --output text --region "$AWS_REGION")

echo "Instance launching: $INSTANCE_ID"
echo "INSTANCE_ID=$INSTANCE_ID" >> "$(dirname "$0")/.infra-state"

echo "--- Waiting for instance to be running ---"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"

PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text --region "$AWS_REGION")

echo "PUBLIC_IP=$PUBLIC_IP" >> "$(dirname "$0")/.infra-state"

echo ""
echo "=== Step 3 complete ==="
echo "Instance ID: $INSTANCE_ID"
echo "Public IP:   $PUBLIC_IP"
echo ""
echo "IMPORTANT: The app takes 1-3 minutes AFTER this to finish installing"
echo "(user-data is still running in the background). Wait ~2 minutes, then try:"
echo "   http://$PUBLIC_IP:8000"
echo ""
echo "If it doesn't load after a few minutes, check the deploy log via SSM:"
echo "   aws ssm start-session --target $INSTANCE_ID --region $AWS_REGION"
echo "   sudo cat /var/log/cloudfolio-userdata.log"
echo ""
echo "Screenshot suggestion: AWS Console -> EC2 -> Instances (show running instance, "
echo "its security group, and IAM instance profile)"
echo "Next: run 04-s3-setup.sh"
