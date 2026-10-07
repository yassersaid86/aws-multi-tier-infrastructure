import boto3
import time

# ==============================
# AWS SESSION
# ==============================

session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

rds = session.client("rds")
ec2 = session.client("ec2")


# ==============================
# CONFIGURATION
# ==============================

VPC_ID = "vpc-0a43899641820473c"

DB_IDENTIFIER = "webapp-db"
DB_SUBNET_GROUP = "rds-private-subnet-group"
DB_SECURITY_GROUP_NAME = "RDSSG"

DB_INSTANCE_CLASS = "db.t3.micro"
DB_NAME = "webappdb"
DB_USERNAME = "admin"


# ==============================
# FIND RDS SECURITY GROUP
# ==============================

print("\nFinding RDSSG...")

sg_response = ec2.describe_security_groups(
    Filters=[
        {
            "Name": "group-name",
            "Values": [DB_SECURITY_GROUP_NAME]
        },
        {
            "Name": "vpc-id",
            "Values": [VPC_ID]
        }
    ]
)

if not sg_response["SecurityGroups"]:
    raise Exception(
        "RDSSG was not found. "
        "Run rds_security_group.py first."
    )

rds_sg_id = sg_response["SecurityGroups"][0]["GroupId"]

print(f"RDSSG ID: {rds_sg_id}")


# ==============================
# CHECK RDS SUBNET GROUP
# ==============================

print("\nChecking RDS subnet group...")

try:

    subnet_group_response = rds.describe_db_subnet_groups(
        DBSubnetGroupName=DB_SUBNET_GROUP
    )

    subnet_group = subnet_group_response["DBSubnetGroups"][0]

    print(
        f"RDS Subnet Group found: "
        f"{subnet_group['DBSubnetGroupName']}"
    )

except rds.exceptions.DBSubnetGroupNotFoundFault:

    raise Exception(
        "RDS subnet group not found. "
        "Run rds_subnet_group.py first."
    )


# ==============================
# CHECK EXISTING RDS
# ==============================

print("\nChecking if RDS instance already exists...")

try:

    response = rds.describe_db_instances(
        DBInstanceIdentifier=DB_IDENTIFIER
    )

    db = response["DBInstances"][0]

    print("RDS instance already exists.")

except rds.exceptions.DBInstanceNotFoundFault:

    # ==============================
    # CREATE RDS
    # ==============================

    print("\nCreating RDS MySQL Multi-AZ instance...")
    print("This may take several minutes...\n")

    response = rds.create_db_instance(

        # --------------------------
        # Basic Configuration
        # --------------------------

        DBInstanceIdentifier=DB_IDENTIFIER,

        DBInstanceClass=DB_INSTANCE_CLASS,

        Engine="mysql",

        AllocatedStorage=20,

        StorageType="gp3",

        DBName=DB_NAME,

        MasterUsername=DB_USERNAME,

        # AWS manages the password
        # using AWS Secrets Manager
        ManageMasterUserPassword=True,

        Port=3306,

        # --------------------------
        # Network
        # --------------------------

        DBSubnetGroupName=DB_SUBNET_GROUP,

        VpcSecurityGroupIds=[
            rds_sg_id
        ],

        PubliclyAccessible=False,

        # --------------------------
        # Multi-AZ
        # --------------------------

        MultiAZ=True,

        # --------------------------
        # Storage Security
        # --------------------------

        StorageEncrypted=True,

        # --------------------------
        # Backup
        # --------------------------

        # Free Tier restriction
        BackupRetentionPeriod=0,

        CopyTagsToSnapshot=True,

        # --------------------------
        # Maintenance
        # --------------------------

        AutoMinorVersionUpgrade=True,

        # --------------------------
        # Lab Configuration
        # --------------------------

        DeletionProtection=False,

        # --------------------------
        # Tags
        # --------------------------

        Tags=[
            {
                "Key": "Name",
                "Value": "webapp-db"
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

    db = response["DBInstance"]

    print("RDS creation started.")
    print(
        f"Identifier: "
        f"{db['DBInstanceIdentifier']}"
    )


# ==============================
# WAIT FOR AVAILABLE
# ==============================

if db["DBInstanceStatus"] != "available":

    print("\nWaiting for RDS to become AVAILABLE...")

    while True:

        response = rds.describe_db_instances(
            DBInstanceIdentifier=DB_IDENTIFIER
        )

        db = response["DBInstances"][0]

        status = db["DBInstanceStatus"]

        print(f"Current status: {status}")

        if status == "available":
            break

        if status in [
            "failed",
            "incompatible-restore",
            "incompatible-network"
        ]:
            raise Exception(
                f"RDS entered a failed state: {status}"
            )

        time.sleep(30)


# ==============================
# GET FINAL INFORMATION
# ==============================

response = rds.describe_db_instances(
    DBInstanceIdentifier=DB_IDENTIFIER
)

db = response["DBInstances"][0]


# ==============================
# FINAL OUTPUT
# ==============================

print("\n======================================")
print("       RDS CREATED SUCCESSFULLY")
print("======================================")

print(
    f"Identifier       : "
    f"{db['DBInstanceIdentifier']}"
)

print(
    f"Engine           : "
    f"{db['Engine']}"
)

print(
    f"Status           : "
    f"{db['DBInstanceStatus']}"
)

print(
    f"Instance Class   : "
    f"{db['DBInstanceClass']}"
)

print(
    f"Multi-AZ         : "
    f"{db['MultiAZ']}"
)

print(
    f"Encrypted        : "
    f"{db['StorageEncrypted']}"
)

print(
    f"Publicly Access. : "
    f"{db['PubliclyAccessible']}"
)

print(
    f"Port             : "
    f"{db['Endpoint']['Port']}"
)

print(
    f"Endpoint         : "
    f"{db['Endpoint']['Address']}"
)

print(
    f"Subnet Group     : "
    f"{db['DBSubnetGroup']['DBSubnetGroupName']}"
)

print(
    f"AZ               : "
    f"{db['AvailabilityZone']}"
)


# ==============================
# SECURITY GROUPS
# ==============================

print("\nVPC Security Groups:")

for sg in db.get("VpcSecurityGroups", []):

    sg_id = sg.get(
        "VpcSecurityGroupId",
        "Unknown"
    )

    sg_status = sg.get(
        "Status",
        "Unknown"
    )

    print(
        f"  - {sg_id} "
        f"(Status: {sg_status})"
    )


# ==============================
# SECRETS MANAGER
# ==============================

if "MasterUserSecret" in db:

    print("\nAWS Secrets Manager:")

    print(
        f"Secret ARN       : "
        f"{db['MasterUserSecret']['SecretArn']}"
    )


# ==============================
# COMPLETE
# ==============================

print("\n======================================")
print("RDS SETUP COMPLETE")
print("======================================")