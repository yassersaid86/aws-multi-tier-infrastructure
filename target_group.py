import boto3


# =========================================================
# AWS SESSION
# =========================================================

session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

elbv2 = session.client("elbv2")
ec2 = session.client("ec2")


# =========================================================
# CONFIGURATION
# =========================================================

VPC_ID = "vpc-0a43899641820473c"

TARGET_GROUP_NAME = "web"

TARGET_PORT = 80

PROTOCOL = "HTTP"


# =========================================================
# FIND WEB-APP SERVERS
# =========================================================

print("Finding Web-App EC2 servers...")


instances_response = ec2.describe_instances(
    Filters=[
        {
            "Name": "instance-state-name",
            "Values": ["running"]
        },
        {
            "Name": "tag:Tier",
            "Values": ["Web-App"]
        }
    ]
)


instance_ids = []

for reservation in instances_response["Reservations"]:

    for instance in reservation["Instances"]:

        instance_id = instance["InstanceId"]

        instance_ids.append(instance_id)

        print(
            f"Found: {instance_id} "
            f"Private IP: {instance.get('PrivateIpAddress')}"
        )


if len(instance_ids) < 2:
    raise Exception(
        "Expected 2 running Web-App EC2 instances, "
        f"but found {len(instance_ids)}."
    )


# =========================================================
# CHECK IF TARGET GROUP ALREADY EXISTS
# =========================================================

print("\nChecking Target Group...")


target_group_arn = None


try:

    response = elbv2.describe_target_groups(
        Names=[TARGET_GROUP_NAME]
    )

    if response["TargetGroups"]:

        target_group = response["TargetGroups"][0]

        target_group_arn = target_group["TargetGroupArn"]

        print(
            f"Target Group already exists: "
            f"{target_group_arn}"
        )

except elbv2.exceptions.TargetGroupNotFoundException:

    target_group_arn = None


# =========================================================
# CREATE TARGET GROUP
# =========================================================

if target_group_arn is None:

    print("\nCreating Target Group...")

    response = elbv2.create_target_group(

        Name=TARGET_GROUP_NAME,

        Protocol=PROTOCOL,

        Port=TARGET_PORT,

        VpcId=VPC_ID,

        TargetType="instance",

        HealthCheckProtocol="HTTP",

        HealthCheckPort="80",

        HealthCheckEnabled=True,

        HealthCheckPath="/",

        HealthCheckIntervalSeconds=30,

        HealthCheckTimeoutSeconds=5,

        HealthyThresholdCount=2,

        UnhealthyThresholdCount=2,

        Matcher={
            "HttpCode": "200"
        },

        Tags=[
            {
                "Key": "Project",
                "Value": "Multi-Tier-Web-App"
            },
            {
                "Key": "Tier",
                "Value": "Web-App"
            }
        ]
    )

    target_group = response["TargetGroups"][0]

    target_group_arn = target_group["TargetGroupArn"]

    print("Target Group created successfully.")

else:

    print("Using existing Target Group.")


# =========================================================
# REGISTER EC2 INSTANCES
# =========================================================

print("\nRegistering EC2 instances as targets...")


targets = []

for instance_id in instance_ids:

    targets.append(
        {
            "Id": instance_id,
            "Port": TARGET_PORT
        }
    )


elbv2.register_targets(

    TargetGroupArn=target_group_arn,

    Targets=targets
)


print("EC2 instances registered successfully.")


# =========================================================
# GET TARGET GROUP INFORMATION
# =========================================================

target_group_info = elbv2.describe_target_groups(
    TargetGroupArns=[target_group_arn]
)


target_group = target_group_info["TargetGroups"][0]


# =========================================================
# CHECK TARGET HEALTH
# =========================================================

print("\nChecking Target Health...")

health_response = elbv2.describe_target_health(
    TargetGroupArn=target_group_arn
)


# =========================================================
# FINAL OUTPUT
# =========================================================

print("\n")
print("=" * 60)
print("             TARGET GROUP CREATED")
print("=" * 60)

print(f"\nName       : {target_group['TargetGroupName']}")

print(f"ARN        : {target_group['TargetGroupArn']}")

print(f"Protocol   : {target_group['Protocol']}")

print(f"Port       : {target_group['Port']}")

print(f"VPC ID     : {target_group['VpcId']}")

print(
    f"Health Path: "
    f"{target_group['HealthCheckPath']}"
)

print("\nTargets:")

for target in health_response["TargetHealthDescriptions"]:

    print(
        f"\nInstance ID : {target['Target']['Id']}"
    )

    print(
        f"Port        : {target['Target']['Port']}"
    )

    print(
        f"Health      : "
        f"{target['TargetHealth']['State']}"
    )


print("\n")
print("=" * 60)
print("          TARGET GROUP SETUP COMPLETED")
print("=" * 60)