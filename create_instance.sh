#!/bin/bash
#set -x
set -e

# Default values
YAML_FILE="resources.yaml"
INSTANCE_TYPE=$(grep 'instance_type' $YAML_FILE | awk '{print $2}')

# Parse command-line options
while getopts ":t:" opt; do
  case $opt in
    t)
      INSTANCE_TYPE=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

# Print current account name and AWS user in table format
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Arn' --output text --no-cli-pager)
REGION=$(aws configure get region --no-cli-pager)

echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
# Load variables from YAML file
SECURITY_GROUP_ID=$(grep 'security_group_id' $YAML_FILE | awk '{print $2}')
EBS_AZ=$(grep 'ebs_az' $YAML_FILE | awk '{print $2}')
EBS_VOLUME_ID=$(grep 'ebs_volume_id' $YAML_FILE | awk '{print $2}')
SSH_KEY_NAME=$(grep 'ssh_key_name' $YAML_FILE | awk '{print $2}')
LOCAL_SSH_KEY_PATH=$(grep 'local_ssh_key_path' $YAML_FILE | awk '{print $2}')
MY_PUBLIC_IP=$(curl -s https://api.ipify.org)
# Fetch the latest Ubuntu AMI ID
AMI_ID=$(aws ec2 describe-images --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-*-*-amd64-server-*" \
    "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text --no-cli-pager)

# Create an EC2 instance with a 40GB disk
INSTANCE_ID=$(aws ec2 run-instances --image-id $AMI_ID \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $SSH_KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --query 'Instances[0].InstanceId' \
    --placement AvailabilityZone=$EBS_AZ \
    --output text --no-cli-pager)

echo "EC2 instance created with ID: $INSTANCE_ID"
echo $INSTANCE_ID > instance_id.txt

# Wait for the instance to be in the running state
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --no-cli-pager
echo "EC2 instance is now running."

# Attach the EBS volume to the instance
aws ec2 attach-volume --volume-id $EBS_VOLUME_ID --instance-id $INSTANCE_ID --device /dev/sdf --output text --no-cli-pager

echo "EBS volume $VOLUME_ID attached to instance $INSTANCE_ID"

# Get the public IP address of the instance
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text --no-cli-pager)

echo "EC2 instance is accessible at IP: $PUBLIC_IP"

# Save the instance ID and public IP to a file
echo $PUBLIC_IP > instance_ip.txt

# Mount the EBS volume and configure iptables in a single SSH session
echo "Waiting for instance to be ready..."
sleep 5
# Try to establish SSH connection with retries
MAX_RETRIES=10
RETRY_DELAY=3
attempt=1
connected=false

while [ $attempt -le $MAX_RETRIES ] && [ "$connected" = false ]; do
  echo "Attempting to connect to instance (attempt $attempt of $MAX_RETRIES)..."
  if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i $LOCAL_SSH_KEY_PATH ubuntu@$PUBLIC_IP exit 2>/dev/null; then
    connected=true
    echo "Successfully connected to instance"
  else
    echo "Connection attempt failed. Retrying in $RETRY_DELAY seconds..."
    sleep $RETRY_DELAY
    ((attempt++))
  fi
done

if [ "$connected" = false ]; then
  echo "Failed to connect to instance after $MAX_RETRIES attempts"
  exit 1
fi

echo "Configuring instance..."
ssh -o StrictHostKeyChecking=no -i $LOCAL_SSH_KEY_PATH ubuntu@$PUBLIC_IP <<EOF
  set -x
  sudo ufw allow from $MY_PUBLIC_IP to any port 22 proto tcp
  sudo ufw allow 443/tcp
  sudo ufw delete allow 22
  sudo ufw enable
  sudo ufw status verbose
EOF