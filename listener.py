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

ALB_NAME = "web-alb"

TARGET_GROUP_NAME = "web"

LISTENER_PORT = 80

PROTOCOL = "HTTP"


# =========================================================
# FIND ALB
# =========================================================

print("Finding Application Load Balancer...")

alb_response = elbv2.describe_load_balancers(
    Names=[ALB_NAME]
)

if not alb_response["LoadBalancers"]:
    raise Exception(
        "ALB 'web-alb' was not found. "
        "Run load_balancer.py first."
    )

ALB = alb_response["LoadBalancers"][0]

ALB_ARN = ALB["LoadBalancerArn"]

ALB_DNS = ALB["DNSName"]

print(f"ALB found: {ALB_ARN}")


# =========================================================
# FIND TARGET GROUP
# =========================================================

print("\nFinding Target Group...")

try:

    target_group_response = elbv2.describe_target_groups(
        Names=[TARGET_GROUP_NAME]
    )

except elbv2.exceptions.TargetGroupNotFoundException:

    raise Exception(
        "Target Group 'web' was not found. "
        "Run target_group.py first."
    )


if not target_group_response["TargetGroups"]:

    raise Exception(
        "Target Group 'web' was not found."
    )


TARGET_GROUP_ARN = target_group_response[
    "TargetGroups"
][0]["TargetGroupArn"]

print(f"Target Group found: {TARGET_GROUP_ARN}")


# =========================================================
# CHECK EXISTING LISTENERS
# =========================================================

print("\nChecking existing listeners...")

listeners_response = elbv2.describe_listeners(
    LoadBalancerArn=ALB_ARN
)

existing_listener = None

for listener in listeners_response["Listeners"]:

    if listener["Port"] == LISTENER_PORT:

        existing_listener = listener

        break


# =========================================================
# CREATE LISTENER
# =========================================================

if existing_listener:

    LISTENER_ARN = existing_listener["ListenerArn"]

    print(
        f"Listener already exists: "
        f"{LISTENER_ARN}"
    )

else:

    print("\nCreating HTTP Listener on port 80...")

    listener_response = elbv2.create_listener(

        LoadBalancerArn=ALB_ARN,

        Protocol=PROTOCOL,

        Port=LISTENER_PORT,

        DefaultActions=[
            {
                "Type": "forward",

                "TargetGroupArn": TARGET_GROUP_ARN
            }
        ]
    )

    LISTENER_ARN = listener_response[
        "Listeners"
    ][0]["ListenerArn"]

    print("Listener created successfully.")


# =========================================================
# IF LISTENER EXISTS
# MAKE SURE IT FORWARDS TO TARGET GROUP
# =========================================================

if existing_listener:

    print(
        "\nUpdating Listener default action "
        "to Target Group 'web'..."
    )

    elbv2.modify_listener(

        ListenerArn=LISTENER_ARN,

        DefaultActions=[
            {
                "Type": "forward",

                "TargetGroupArn": TARGET_GROUP_ARN
            }
        ]
    )

    print("Listener updated successfully.")


# =========================================================
# GET FINAL LISTENER INFORMATION
# =========================================================

final_listener_response = elbv2.describe_listeners(
    ListenerArns=[LISTENER_ARN]
)

listener = final_listener_response[
    "Listeners"
][0]


# =========================================================
# FINAL OUTPUT
# =========================================================

print("\n")
print("=" * 65)
print("             LISTENER CREATED")
print("=" * 65)

print(f"\nListener ARN : {listener['ListenerArn']}")

print(f"Protocol     : {listener['Protocol']}")

print(f"Port         : {listener['Port']}")

print(f"ALB          : {ALB_NAME}")

print(f"Target Group : {TARGET_GROUP_NAME}")

print(f"Target ARN   : {TARGET_GROUP_ARN}")

print("\n")
print("=" * 65)
print("            LISTENER SETUP COMPLETED")
print("=" * 65)

print("\nALB URL:")
print(f"http://{ALB_DNS}")