import boto3


# =========================================================
# AWS SESSION
# =========================================================

session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

ec2 = session.client("ec2")


# =========================================================
# CONFIGURATION
# =========================================================

VPC_ID = "vpc-0a43899641820473c"

PRIVATE_SUBNET_A = "subnet-07a027f8b854f114a"
PRIVATE_SUBNET_B = "subnet-0de4f1e9875766ba1"

AMI_ID = "ami-07b31e16db6bbfb9e"

KEY_NAME = "myFirstKeypair"

INSTANCE_TYPE = "t3.micro"

WEB_SG_NAME = "websG"


# =========================================================
# FIND SECURITY GROUP
# =========================================================

print("Finding websG Security Group...")

sg_response = ec2.describe_security_groups(
    Filters=[
        {
            "Name": "group-name",
            "Values": [WEB_SG_NAME]
        },
        {
            "Name": "vpc-id",
            "Values": [VPC_ID]
        }
    ]
)

if not sg_response["SecurityGroups"]:
    raise Exception("Security Group websG was not found!")

WEB_SG_ID = sg_response["SecurityGroups"][0]["GroupId"]

print(f"websG found: {WEB_SG_ID}")


# =========================================================
# GET AMI INFORMATION
# =========================================================

print("\nGetting AMI information...")

ami_response = ec2.describe_images(
    ImageIds=[AMI_ID]
)

if not ami_response["Images"]:
    raise Exception("AMI was not found!")

ami = ami_response["Images"][0]

ROOT_DEVICE_NAME = ami["RootDeviceName"]

print(f"AMI: {AMI_ID}")
print(f"Root Device: {ROOT_DEVICE_NAME}")


# =========================================================
# CREATE ENCRYPTED EBS CONFIGURATION
# =========================================================

root_device = None

for device in ami.get("BlockDeviceMappings", []):

    if device.get("DeviceName") == ROOT_DEVICE_NAME:

        if "Ebs" in device:
            root_device = device["Ebs"]

        break


if root_device is None:
    raise Exception("Could not find root EBS configuration in AMI!")


ebs_config = {
    "VolumeSize": root_device.get("VolumeSize", 8),
    "VolumeType": root_device.get("VolumeType", "gp3"),
    "DeleteOnTermination": True,
    "Encrypted": True
}


# Preserve IOPS if available
if "Iops" in root_device:
    ebs_config["Iops"] = root_device["Iops"]


# Preserve Throughput if available
if "Throughput" in root_device:
    ebs_config["Throughput"] = root_device["Throughput"]


BLOCK_DEVICE_MAPPING = {
    "DeviceName": ROOT_DEVICE_NAME,
    "Ebs": ebs_config
}


print("\nEBS configuration:")
print(f"Volume Size : {ebs_config['VolumeSize']} GB")
print(f"Volume Type : {ebs_config['VolumeType']}")
print(f"Encrypted   : {ebs_config['Encrypted']}")


# =========================================================
# USER DATA - SERVER 1
# =========================================================

USER_DATA_SERVER_1 = """#!/bin/bash

yum update -y

yum install -y httpd

systemctl start httpd
systemctl enable httpd

echo "This is Server 1 - AWS Region US-EAST-1 - Availability Zone US-EAST-1A" > /var/www/html/index.html
"""


# =========================================================
# USER DATA - SERVER 2
# =========================================================

USER_DATA_SERVER_2 = """#!/bin/bash

yum update -y

yum install -y httpd

systemctl start httpd
systemctl enable httpd

echo "This is Server 2 - AWS Region US-EAST-1 - Availability Zone US-EAST-1B" > /var/www/html/index.html
"""


# =========================================================
# LAUNCH SERVER 1
# =========================================================

print("\nLaunching Server 1...")

server_1_response = ec2.run_instances(

    ImageId=AMI_ID,

    InstanceType=INSTANCE_TYPE,

    KeyName=KEY_NAME,

    MinCount=1,

    MaxCount=1,

    NetworkInterfaces=[
        {
            "DeviceIndex": 0,

            "SubnetId": PRIVATE_SUBNET_A,

            "AssociatePublicIpAddress": False,

            "Groups": [
                WEB_SG_ID
            ]
        }
    ],

    BlockDeviceMappings=[
        BLOCK_DEVICE_MAPPING
    ],

    UserData=USER_DATA_SERVER_1,

    TagSpecifications=[
        {
            "ResourceType": "instance",

            "Tags": [
                {
                    "Key": "Name",
                    "Value": "Web-App-Server-1"
                },
                {
                    "Key": "Project",
                    "Value": "Multi-Tier-Web-App"
                },
                {
                    "Key": "Tier",
                    "Value": "Web-App"
                }
            ]
        }
    ]
)


SERVER_1_ID = server_1_response["Instances"][0]["InstanceId"]

print(f"Server 1 ID: {SERVER_1_ID}")


# =========================================================
# LAUNCH SERVER 2
# =========================================================

print("\nLaunching Server 2...")

server_2_response = ec2.run_instances(

    ImageId=AMI_ID,

    InstanceType=INSTANCE_TYPE,

    KeyName=KEY_NAME,

    MinCount=1,

    MaxCount=1,

    NetworkInterfaces=[
        {
            "DeviceIndex": 0,

            "SubnetId": PRIVATE_SUBNET_B,

            "AssociatePublicIpAddress": False,

            "Groups": [
                WEB_SG_ID
            ]
        }
    ],

    BlockDeviceMappings=[
        BLOCK_DEVICE_MAPPING
    ],

    UserData=USER_DATA_SERVER_2,

    TagSpecifications=[
        {
            "ResourceType": "instance",

            "Tags": [
                {
                    "Key": "Name",
                    "Value": "Web-App-Server-2"
                },
                {
                    "Key": "Project",
                    "Value": "Multi-Tier-Web-App"
                },
                {
                    "Key": "Tier",
                    "Value": "Web-App"
                }
            ]
        }
    ]
)


SERVER_2_ID = server_2_response["Instances"][0]["InstanceId"]

print(f"Server 2 ID: {SERVER_2_ID}")


# =========================================================
# WAIT UNTIL BOTH INSTANCES ARE RUNNING
# =========================================================

print("\nWaiting for both servers to become RUNNING...")

ec2.get_waiter("instance_running").wait(
    InstanceIds=[
        SERVER_1_ID,
        SERVER_2_ID
    ]
)


print("\nBoth servers are RUNNING!")


# =========================================================
# GET FINAL INSTANCE INFORMATION
# =========================================================

instances_response = ec2.describe_instances(
    InstanceIds=[
        SERVER_1_ID,
        SERVER_2_ID
    ]
)


print("\n")
print("=" * 55)
print("       EC2 SERVERS CREATED SUCCESSFULLY")
print("=" * 55)


for reservation in instances_response["Reservations"]:

    for instance in reservation["Instances"]:

        instance_name = "Unknown"

        for tag in instance.get("Tags", []):

            if tag["Key"] == "Name":
                instance_name = tag["Value"]


        print("\n---------------------------------------")

        print(f"Name        : {instance_name}")

        print(f"Instance ID : {instance['InstanceId']}")

        print(f"Private IP  : {instance.get('PrivateIpAddress')}")

        print(f"Subnet ID   : {instance['SubnetId']}")

        print(
            f"AZ          : "
            f"{instance['Placement']['AvailabilityZone']}"
        )

        print(
            f"State       : "
            f"{instance['State']['Name']}"
        )

        print(
            f"Public IP   : "
            f"{instance.get('PublicIpAddress', 'None')}"
        )


print("\n")
print("=" * 55)
print("             EC2 SETUP COMPLETED")
print("=" * 55)