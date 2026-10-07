import boto3
import time
import base64




session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

ec2 = session.client("ec2")
elbv2 = session.client("elbv2")
autoscaling = session.client("autoscaling")


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

TARGET_GROUP_NAME = "web"

LAUNCH_TEMPLATE_NAME = "web-app-launch-template"

ASG_NAME = "web-app-asg"

MIN_SIZE = 2

DESIRED_CAPACITY = 2

MAX_SIZE = 4




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

print(f"websG: {WEB_SG_ID}")


# =========================================================
# FIND TARGET GROUP
# =========================================================

print("\nFinding Target Group...")

try:

    tg_response = elbv2.describe_target_groups(
        Names=[TARGET_GROUP_NAME]
    )

except elbv2.exceptions.TargetGroupNotFoundException:

    raise Exception(
        "Target Group 'web' was not found. "
        "Run target_group.py first."
    )


if not tg_response["TargetGroups"]:
    raise Exception("Target Group 'web' was not found!")


TARGET_GROUP_ARN = tg_response["TargetGroups"][0]["TargetGroupArn"]

print(f"Target Group: {TARGET_GROUP_ARN}")


# =========================================================
# GET AMI ROOT DEVICE
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
# BUILD ENCRYPTED EBS CONFIGURATION
# =========================================================

root_device = None

for device in ami.get("BlockDeviceMappings", []):

    if device.get("DeviceName") == ROOT_DEVICE_NAME:

        if "Ebs" in device:
            root_device = device["Ebs"]

        break


if root_device is None:
    raise Exception(
        "Could not find root EBS configuration!"
    )


ebs_config = {
    "VolumeSize": root_device.get("VolumeSize", 8),
    "VolumeType": root_device.get("VolumeType", "gp3"),
    "DeleteOnTermination": True,
    "Encrypted": True
}


if "Iops" in root_device:
    ebs_config["Iops"] = root_device["Iops"]


if "Throughput" in root_device:
    ebs_config["Throughput"] = root_device["Throughput"]


BLOCK_DEVICE_MAPPING = {
    "DeviceName": ROOT_DEVICE_NAME,
    "Ebs": ebs_config
}


# =========================================================
# USER DATA
# =========================================================

USER_DATA = """#!/bin/bash

yum update -y

yum install -y httpd

systemctl start httpd
systemctl enable httpd

echo "This is an Auto Scaling Server - AWS Region US-EAST-1" > /var/www/html/index.html
"""


USER_DATA_ENCODED = base64.b64encode(
    USER_DATA.encode("utf-8")
).decode("utf-8")


# =========================================================
# CHECK LAUNCH TEMPLATE
# =========================================================

print("\nChecking Launch Template...")

launch_template_id = None


try:

    response = ec2.describe_launch_templates(
        LaunchTemplateNames=[
            LAUNCH_TEMPLATE_NAME
        ]
    )

    if response["LaunchTemplates"]:

        launch_template_id = response[
            "LaunchTemplates"
        ][0]["LaunchTemplateId"]

        print(
            f"Launch Template already exists: "
            f"{launch_template_id}"
        )

except ec2.exceptions.ClientError:

    launch_template_id = None


# =========================================================
# CREATE LAUNCH TEMPLATE
# =========================================================

if launch_template_id is None:

    print("\nCreating Launch Template...")

    launch_template_response = ec2.create_launch_template(

        LaunchTemplateName=LAUNCH_TEMPLATE_NAME,

        VersionDescription="Web App Auto Scaling Launch Template",

        LaunchTemplateData={

            "ImageId": AMI_ID,

            "InstanceType": INSTANCE_TYPE,

            "KeyName": KEY_NAME,

            "SecurityGroupIds": [
                WEB_SG_ID
            ],

            "BlockDeviceMappings": [
                BLOCK_DEVICE_MAPPING
            ],

            "UserData": USER_DATA_ENCODED,

            "TagSpecifications": [
                {
                    "ResourceType": "instance",

                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "ASG-Web-App-Server"
                        },
                        {
                            "Key": "Project",
                            "Value": "Multi-Tier-Web-App"
                        },
                        {
                            "Key": "Tier",
                            "Value": "Web-App"
                        },
                        {
                            "Key": "ManagedBy",
                            "Value": "AutoScaling"
                        }
                    ]
                }
            ]
        }
    )

    launch_template_id = (
        launch_template_response[
            "LaunchTemplate"
        ]["LaunchTemplateId"]
    )

    print(
        f"Launch Template created: "
        f"{launch_template_id}"
    )

else:

    print("Using existing Launch Template.")


# =========================================================
# CHECK AUTO SCALING GROUP
# =========================================================

print("\nChecking Auto Scaling Group...")

asg_exists = False


asg_response = autoscaling.describe_auto_scaling_groups(
    AutoScalingGroupNames=[
        ASG_NAME
    ]
)


if asg_response["AutoScalingGroups"]:

    asg_exists = True

    print("Auto Scaling Group already exists.")


# =========================================================
# CREATE AUTO SCALING GROUP
# =========================================================

if not asg_exists:

    print("\nCreating Auto Scaling Group...")

    autoscaling.create_auto_scaling_group(

        AutoScalingGroupName=ASG_NAME,

        LaunchTemplate={
            "LaunchTemplateId": launch_template_id,

            "Version": "$Latest"
        },

        MinSize=MIN_SIZE,

        MaxSize=MAX_SIZE,

        DesiredCapacity=DESIRED_CAPACITY,

        VPCZoneIdentifier=",".join([
            PRIVATE_SUBNET_A,
            PRIVATE_SUBNET_B
        ]),

        TargetGroupARNs=[
            TARGET_GROUP_ARN
        ],

        HealthCheckType="ELB",

        HealthCheckGracePeriod=180,

        Tags=[
            {
                "Key": "Name",
                "Value": "ASG-Web-App-Server",
                "PropagateAtLaunch": True
            },
            {
                "Key": "Project",
                "Value": "Multi-Tier-Web-App",
                "PropagateAtLaunch": True
            },
            {
                "Key": "Tier",
                "Value": "Web-App",
                "PropagateAtLaunch": True
            },
            {
                "Key": "ManagedBy",
                "Value": "AutoScaling",
                "PropagateAtLaunch": True
            }
        ]
    )

    print("Auto Scaling Group created successfully.")

else:

    print("Using existing Auto Scaling Group.")


# =========================================================
# CREATE TARGET TRACKING POLICY
# =========================================================

print("\nConfiguring CPU Target Tracking...")


autoscaling.put_scaling_policy(

    AutoScalingGroupName=ASG_NAME,

    PolicyName="CPU-Target-Tracking-50",

    PolicyType="TargetTrackingScaling",

    TargetTrackingConfiguration={

        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ASGAverageCPUUtilization"
        },

        "TargetValue": 50.0,

        "DisableScaleIn": False
    }
)


print("CPU Target Tracking configured.")
print("Target CPU: 50%")



# WAIT FOR ASG INSTANCES
# =========================================================

print("\nWaiting for Auto Scaling instances...")

for i in range(12):

    asg_response = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            ASG_NAME
        ]
    )

    asg = asg_response["AutoScalingGroups"][0]

    instances = asg.get("Instances", [])

    print(
        f"Check {i + 1}/12 - "
        f"Instances: {len(instances)}"
    )

    if len(instances) >= DESIRED_CAPACITY:
        break

    time.sleep(15)


# =========================================================
# GET ASG INSTANCES
# =========================================================

asg_response = autoscaling.describe_auto_scaling_groups(
    AutoScalingGroupNames=[
        ASG_NAME
    ]
)

asg = asg_response["AutoScalingGroups"][0]

asg_instance_ids = [
    instance["InstanceId"]
    for instance in asg.get("Instances", [])
]


# =========================================================
# GET INSTANCE INFORMATION
# =========================================================

print("\nGetting ASG instance information...")

if asg_instance_ids:

    instances_response = ec2.describe_instances(
        InstanceIds=asg_instance_ids
    )

    print("\n")
    print("=" * 65)
    print("          AUTO SCALING INSTANCES")
    print("=" * 65)

    for reservation in instances_response["Reservations"]:

        for instance in reservation["Instances"]:

            print("\n---------------------------------------")

            print(
                f"Instance ID : "
                f"{instance['InstanceId']}"
            )

            print(
                f"Private IP  : "
                f"{instance.get('PrivateIpAddress')}"
            )

            print(
                f"Subnet ID   : "
                f"{instance['SubnetId']}"
            )

            print(
                f"AZ          : "
                f"{instance['Placement']['AvailabilityZone']}"
            )

            print(
                f"State       : "
                f"{instance['State']['Name']}"
            )


# =========================================================
# FINAL ASG INFORMATION
# =========================================================

print("\n")
print("=" * 65)
print("           AUTO SCALING COMPLETED")
print("=" * 65)

print(f"\nASG Name       : {ASG_NAME}")

print(f"Min Size       : {MIN_SIZE}")

print(f"Desired Size   : {DESIRED_CAPACITY}")

print(f"Max Size       : {MAX_SIZE}")

print(f"Target Group   : {TARGET_GROUP_NAME}")

print("Health Check   : ELB")

print("CPU Target     : 50%")

print("\nPrivate Subnets:")

print(f"  - {PRIVATE_SUBNET_A}")

print(f"  - {PRIVATE_SUBNET_B}")

print("\n")
print("=" * 65)