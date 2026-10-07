import boto3


# =========================================================
# AWS SESSION
# =========================================================

session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

rds = session.client("rds")


# =========================================================
# CONFIGURATION
# =========================================================

PRIVATE_SUBNET_A = "subnet-07a027f8b854f114a"

PRIVATE_SUBNET_B = "subnet-0de4f1e9875766ba1"

SUBNET_GROUP_NAME = "rds-private-subnet-group"

SUBNET_GROUP_DESCRIPTION = (
    "Private subnet group for Multi-AZ RDS"
)


# =========================================================
# CHECK IF SUBNET GROUP EXISTS
# =========================================================

print("Checking RDS Subnet Group...")

subnet_group_exists = False


try:

    response = rds.describe_db_subnet_groups(
        DBSubnetGroupName=SUBNET_GROUP_NAME
    )

    if response["DBSubnetGroups"]:

        subnet_group_exists = True

        print(
            f"RDS Subnet Group already exists: "
            f"{SUBNET_GROUP_NAME}"
        )


except rds.exceptions.DBSubnetGroupNotFoundFault:

    subnet_group_exists = False


# =========================================================
# CREATE SUBNET GROUP
# =========================================================

if not subnet_group_exists:

    print("\nCreating RDS Subnet Group...")

    response = rds.create_db_subnet_group(

        DBSubnetGroupName=SUBNET_GROUP_NAME,

        DBSubnetGroupDescription=SUBNET_GROUP_DESCRIPTION,

        SubnetIds=[
            PRIVATE_SUBNET_A,
            PRIVATE_SUBNET_B
        ],

        Tags=[
            {
                "Key": "Name",
                "Value": SUBNET_GROUP_NAME
            },
            {
                "Key": "Project",
                "Value": "Multi-Tier-Web-App"
            },
            {
                "Key": "Tier",
                "Value": "Database"
            }
        ]
    )

    print("RDS Subnet Group created successfully.")

    subnet_group = response["DBSubnetGroup"]

else:

    response = rds.describe_db_subnet_groups(
        DBSubnetGroupName=SUBNET_GROUP_NAME
    )

    subnet_group = response["DBSubnetGroups"][0]


# =========================================================
# FINAL OUTPUT
# =========================================================

print("\n")
print("=" * 65)
print("             RDS SUBNET GROUP")
print("=" * 65)

print(
    f"\nName        : "
    f"{subnet_group['DBSubnetGroupName']}"
)

print(
    f"Description : "
    f"{subnet_group['DBSubnetGroupDescription']}"
)

print(
    f"VPC ID      : "
    f"{subnet_group['VpcId']}"
)

print("\nSubnets:")

for subnet in subnet_group["Subnets"]:

    print(
        f"  - {subnet['SubnetIdentifier']} "
        f"({subnet['SubnetStatus']})"
    )

    print(
        f"    AZ: "
        f"{subnet['SubnetAvailabilityZone']['Name']}"
    )


print("\n")
print("=" * 65)
print("          RDS SUBNET GROUP READY")
print("=" * 65)