import boto3

# ==============================
# AWS SESSION
# ==============================

session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

ec2 = session.client("ec2")
elbv2 = session.client("elbv2")
autoscaling = session.client("autoscaling")
rds = session.client("rds")


# ==============================
# CONFIGURATION
# ==============================

VPC_ID = "vpc-0a43899641820473c"

TARGET_GROUP_NAME = "web"
ALB_NAME = "web-alb"
ASG_NAME = "web-app-asg"
DB_IDENTIFIER = "webapp-db"


print("\n")
print("==============================================")
print("        MULTI-TIER AWS FINAL TEST")
print("==============================================")


# ============================================================
# 1. EC2 / ASG INSTANCES
# ============================================================

print("\n[1] Checking EC2 instances...")

instances_response = ec2.describe_instances(
    Filters=[
        {
            "Name": "vpc-id",
            "Values": [VPC_ID]
        },
        {
            "Name": "instance-state-name",
            "Values": [
                "pending",
                "running"
            ]
        }
    ]
)

instances = []

for reservation in instances_response["Reservations"]:
    for instance in reservation["Instances"]:

        name = "N/A"
        tier = "N/A"
        managed_by = "Manual"

        for tag in instance.get("Tags", []):

            if tag["Key"] == "Name":
                name = tag["Value"]

            if tag["Key"] == "Tier":
                tier = tag["Value"]

            if tag["Key"] == "ManagedBy":
                managed_by = tag["Value"]

        instances.append(instance)

        print(
            f"Instance: {instance['InstanceId']} | "
            f"State: {instance['State']['Name']} | "
            f"Name: {name} | "
            f"Tier: {tier} | "
            f"ManagedBy: {managed_by}"
        )

print(f"\nTotal running/pending instances: {len(instances)}")


# ============================================================
# 2. TARGET GROUP
# ============================================================

print("\n[2] Checking Target Group...")

tg_response = elbv2.describe_target_groups(
    Names=[TARGET_GROUP_NAME]
)

target_group = tg_response["TargetGroups"][0]

target_group_arn = target_group["TargetGroupArn"]

print(f"Target Group : {target_group['TargetGroupName']}")
print(f"Protocol     : {target_group['Protocol']}")
print(f"Port         : {target_group['Port']}")
print(f"Health Check : {target_group['HealthCheckPath']}")


# ============================================================
# 3. TARGET HEALTH
# ============================================================

print("\n[3] Checking Target Health...")

health_response = elbv2.describe_target_health(
    TargetGroupArn=target_group_arn
)

healthy_count = 0

for target in health_response["TargetHealthDescriptions"]:

    instance_id = target["Target"]["Id"]
    state = target["TargetHealth"]["State"]

    print(
        f"Target: {instance_id} | "
        f"Health: {state}"
    )

    if state == "healthy":
        healthy_count += 1


print(f"\nHealthy targets: {healthy_count}")


# ============================================================
# 4. LOAD BALANCER
# ============================================================

print("\n[4] Checking Application Load Balancer...")

alb_response = elbv2.describe_load_balancers(
    Names=[ALB_NAME]
)

alb = alb_response["LoadBalancers"][0]

print(f"ALB Name       : {alb['LoadBalancerName']}")
print(f"State          : {alb['State']['Code']}")
print(f"Scheme         : {alb['Scheme']}")
print(f"Type           : {alb['Type']}")
print(f"DNS Name       : {alb['DNSName']}")


# ============================================================
# 5. LISTENER
# ============================================================

print("\n[5] Checking ALB Listener...")

listeners_response = elbv2.describe_listeners(
    LoadBalancerArn=alb["LoadBalancerArn"]
)

for listener in listeners_response["Listeners"]:

    print(
        f"Listener: "
        f"{listener['Protocol']} "
        f"Port {listener['Port']}"
    )


# ============================================================
# 6. AUTO SCALING GROUP
# ============================================================

print("\n[6] Checking Auto Scaling Group...")

asg_response = autoscaling.describe_auto_scaling_groups(
    AutoScalingGroupNames=[ASG_NAME]
)

if not asg_response["AutoScalingGroups"]:
    raise Exception("Auto Scaling Group not found.")

asg = asg_response["AutoScalingGroups"][0]

print(f"ASG Name       : {asg['AutoScalingGroupName']}")
print(f"Min Size       : {asg['MinSize']}")
print(f"Desired        : {asg['DesiredCapacity']}")
print(f"Max Size       : {asg['MaxSize']}")
print(f"Health Check   : {asg['HealthCheckType']}")

print("\nASG Instances:")

for instance in asg["Instances"]:

    print(
        f"  - {instance['InstanceId']} | "
        f"Lifecycle: {instance['LifecycleState']} | "
        f"Health: {instance['HealthStatus']}"
    )


# ============================================================
# 7. RDS
# ============================================================

print("\n[7] Checking RDS...")

db_response = rds.describe_db_instances(
    DBInstanceIdentifier=DB_IDENTIFIER
)

db = db_response["DBInstances"][0]

print(f"Identifier       : {db['DBInstanceIdentifier']}")
print(f"Status           : {db['DBInstanceStatus']}")
print(f"Engine           : {db['Engine']}")
print(f"Multi-AZ         : {db['MultiAZ']}")
print(f"Encrypted        : {db['StorageEncrypted']}")
print(f"Publicly Access. : {db['PubliclyAccessible']}")
print(f"Port             : {db['Endpoint']['Port']}")
print(f"Endpoint         : {db['Endpoint']['Address']}")


# ============================================================
# 8. FINAL SUMMARY
# ============================================================

print("\n")
print("==============================================")
print("              FINAL SUMMARY")
print("==============================================")

print(
    f"EC2 Instances       : {len(instances)}"
)

print(
    f"Healthy ALB Targets : {healthy_count}"
)

print(
    f"ALB State           : {alb['State']['Code']}"
)

print(
    f"ASG Desired         : {asg['DesiredCapacity']}"
)

print(
    f"ASG Max             : {asg['MaxSize']}"
)

print(
    f"RDS Status          : {db['DBInstanceStatus']}"
)

print(
    f"RDS Multi-AZ        : {db['MultiAZ']}"
)

print(
    f"RDS Encrypted       : {db['StorageEncrypted']}"
)

print("\nALB DNS:")
print(alb["DNSName"])

print("\n==============================================")
print("             FINAL TEST COMPLETE")
print("==============================================") 