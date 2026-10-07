import boto3


# =========================================================
# AWS SESSION
# =========================================================

session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

elbv2 = session.client("elbv2")


# =========================================================
# CONFIGURATION
# =========================================================

VPC_ID = "vpc-0a43899641820473c"

PUBLIC_SUBNET_A = "subnet-0e5123dbb4a75933a"
PUBLIC_SUBNET_B = "subnet-076b612bcaadebf07"

ALB_NAME = "web-alb"

ALB_SG_NAME = "ALBSG"

TARGET_GROUP_NAME = "web"


# =========================================================
# FIND ALBSG
# =========================================================

print("Finding ALBSG Security Group...")

ec2 = session.client("ec2")

sg_response = ec2.describe_security_groups(
    Filters=[
        {
            "Name": "group-name",
            "Values": [ALB_SG_NAME]
        },
        {
            "Name": "vpc-id",
            "Values": [VPC_ID]
        }
    ]
)

if not sg_response["SecurityGroups"]:
    raise Exception("ALBSG Security Group was not found!")

ALB_SG_ID = sg_response["SecurityGroups"][0]["GroupId"]

print(f"ALBSG found: {ALB_SG_ID}")


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

print(f"Target Group found: {TARGET_GROUP_ARN}")


# =========================================================
# CHECK IF ALB ALREADY EXISTS
# =========================================================

print("\nChecking if ALB already exists...")

load_balancer_arn = None
load_balancer_dns = None


try:

    alb_response = elbv2.describe_load_balancers(
        Names=[ALB_NAME]
    )

    if alb_response["LoadBalancers"]:

        alb = alb_response["LoadBalancers"][0]

        load_balancer_arn = alb["LoadBalancerArn"]

        load_balancer_dns = alb["DNSName"]

        print("ALB already exists.")

except elbv2.exceptions.LoadBalancerNotFoundException:

    load_balancer_arn = None


# =========================================================
# CREATE APPLICATION LOAD BALANCER
# =========================================================

if load_balancer_arn is None:

    print("\nCreating Application Load Balancer...")

    alb_response = elbv2.create_load_balancer(

        Name=ALB_NAME,

        Subnets=[
            PUBLIC_SUBNET_A,
            PUBLIC_SUBNET_B
        ],

        SecurityGroups=[
            ALB_SG_ID
        ],

        Scheme="internet-facing",

        Type="application",

        IpAddressType="ipv4",

        Tags=[
            {
                "Key": "Name",
                "Value": ALB_NAME
            },
            {
                "Key": "Project",
                "Value": "Multi-Tier-Web-App"
            },
            {
                "Key": "Tier",
                "Value": "Load-Balancer"
            }
        ]
    )

    alb = alb_response["LoadBalancers"][0]

    load_balancer_arn = alb["LoadBalancerArn"]

    load_balancer_dns = alb["DNSName"]

    print("ALB created successfully.")

else:

    print("Using existing ALB.")


# =========================================================
# WAIT UNTIL ALB IS ACTIVE
# =========================================================

print("\nWaiting for ALB to become ACTIVE...")

elbv2.get_waiter(
    "load_balancer_available"
).wait(
    LoadBalancerArns=[
        load_balancer_arn
    ]
)


# =========================================================
# GET FINAL ALB INFORMATION
# =========================================================

final_response = elbv2.describe_load_balancers(
    LoadBalancerArns=[
        load_balancer_arn
    ]
)

alb = final_response["LoadBalancers"][0]


# =========================================================
# FINAL OUTPUT
# =========================================================

print("\n")
print("=" * 65)
print("        APPLICATION LOAD BALANCER CREATED")
print("=" * 65)

print(f"\nName       : {alb['LoadBalancerName']}")

print(f"ARN        : {alb['LoadBalancerArn']}")

print(f"DNS Name   : {alb['DNSName']}")

print(f"Scheme     : {alb['Scheme']}")

print(f"Type       : {alb['Type']}")

print(f"State      : {alb['State']['Code']}")

print(f"VPC ID     : {alb['VpcId']}")

print(f"Security Group: {ALB_SG_ID}")

print("\nSubnets:")

print(f"Public A   : {PUBLIC_SUBNET_A}")

print(f"Public B   : {PUBLIC_SUBNET_B}")


print("\n")
print("=" * 65)
print("             ALB SETUP COMPLETED")
print("=" * 65)

print("\nALB DNS:")
print(alb["DNSName"])