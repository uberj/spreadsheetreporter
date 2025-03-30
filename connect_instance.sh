#!/bin/bash
set -x
set -e

# Check if instance_id.txt exists
if [ ! -f instance_id.txt ]; then
    echo "Error: instance_id.txt not found. Please run create_instance.sh first."
    exit 1
fi

# Read the instance ID from the file
INSTANCE_ID=$(cat instance_id.txt)
YAML_FILE="resources.yaml"
LOCAL_SSH_KEY_PATH=$(grep 'local_ssh_key_path' $YAML_FILE | awk '{print $2}')

# Wait for the instance to be in the "running" state
echo "Waiting for the instance to be in the 'running' state..."
while true; do
    INSTANCE_STATE=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text)
    
    if [ "$INSTANCE_STATE" == "running" ]; then
        echo "Instance is running."
        break
    fi
    
    echo "Current state: $INSTANCE_STATE. Waiting..."
    sleep 5
done

# Fetch the public IP address of the instance
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

if [ -z "$PUBLIC_IP" ]; then
    echo "Error: Could not retrieve the public IP address. Ensure the instance is running."
    exit 1
fi
echo $PUBLIC_IP > instance_ip.txt

# Connect to the instance using SSH
echo "Connecting to EC2 instance at $PUBLIC_IP..."
ssh -o StrictHostKeyChecking=no -i $LOCAL_SSH_KEY_PATH ubuntu@$PUBLIC_IP 