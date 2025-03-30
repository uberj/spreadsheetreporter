#!/bin/bash
set -x
set -e

# Default instance ID to empty
INSTANCE_ID=""

# Parse command-line options
while getopts "i:" opt; do
  case $opt in
    i)
      INSTANCE_ID=$OPTARG
      ;;
    *)
      echo "Usage: $0 [-i instance_id]"
      exit 1
      ;;
  esac
done

# Check if the instance ID file exists if no argument is provided
INSTANCE_ID_FILE="instance_id.txt"
INSTANCE_IP_FILE="instance_ip.txt"

if [ -z "$INSTANCE_ID" ]; then
  if [ ! -f "$INSTANCE_ID_FILE" ]; then
    echo "Instance ID file not found and no instance ID provided. Please ensure the instance has been created and the ID is saved."
    exit 1
  fi
  # Read the instance ID from the file
  INSTANCE_ID=$(cat $INSTANCE_ID_FILE)
fi

# Describe the instance to get attached volumes and identify the root device
ROOT_DEVICE_NAME=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[].Instances[].RootDeviceName" --output text --no-cli-pager)
VOLUME_IDS=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[].Instances[].BlockDeviceMappings[?DeviceName!=\`$ROOT_DEVICE_NAME\`].Ebs.VolumeId" --output text --no-cli-pager)

# Detach each non-root volume
for VOLUME_ID in $VOLUME_IDS; do
  echo "Detaching volume $VOLUME_ID from instance $INSTANCE_ID"
  aws ec2 detach-volume --volume-id $VOLUME_ID --output text --no-cli-pager
done

# Terminate the EC2 instance
aws ec2 terminate-instances --instance-ids $INSTANCE_ID --output text --no-cli-pager

echo "EC2 instance with ID $INSTANCE_ID has been terminated."

# Optionally, remove the instance ID file
rm -f $INSTANCE_ID_FILE 
rm -f $INSTANCE_IP_FILE 