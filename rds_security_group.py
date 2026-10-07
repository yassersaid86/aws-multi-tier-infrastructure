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

WEB_SG_NAME = "websG"

RDS_SG_NAME = "RDSSG"

DB_PORT = 3306


# =========================================================
# FIND WEBSG
# =========================================================

print("Finding websG Security Group...")

web_sg_response = ec2.describe_security_groups(
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

if not web_sg_response["SecurityGroups"]:
    raise Exception(
        "Security Group websG was not found!"
    )

WEB_SG_ID = web_sg_response["SecurityGroups"][0]["GroupId"]

print(f"websG found: {WEB_SG_ID}")


# =========================================================
# CHECK RDS SECURITY GROUP
# =========================================================

print("\nChecking RDSSG...")

rds_sg_id = None

rds_sg_response = ec2.describe_security_groups(
    Filters=[
        {
            "Name": "group-name",
            "Values": [RDS_SG_NAME]
        },
        {
            "Name": "vpc-id",
            "Values": [VPC_ID]
        }
    ]
)

if rds_sg_response["SecurityGroups"]:

    rds_sg = rds_sg_response["SecurityGroups"][0]

    rds_sg_id = rds_sg["GroupId"]

    print(
        f"RDSSG already exists: "
        f"{rds_sg_id}"
    )


# =========================================================
# CREATE RDS SECURITY GROUP
# =========================================================

if rds_sg_id is None:

    print("\nCreating RDS Security Group...")

    create_response = ec2.create_security_group(

        GroupName=RDS_SG_NAME,

        Description=(
            "Security Group for Multi-AZ RDS Database"
        ),

        VpcId=VPC_ID,

        TagSpecifications=[
            {
                "ResourceType": "security-group",

                "Tags": [
                    {
                        "Key": "Name",
                        "Value": RDS_SG_NAME
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
            }
        ]
    )

    rds_sg_id = create_response["GroupId"]

    print(
        f"RDS Security Group created: "
        f"{rds_sg_id}"
    )


# =========================================================
# REMOVE DEFAULT OUTBOUND RULE
# =========================================================

print("\nConfiguring outbound rules...")

try:

    ec2.revoke_security_group_egress(
        GroupId=rds_sg_id,

        IpPermissions=[
            {
                "IpProtocol": "-1",

                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0"
                    }
                ]
            }
        ]
    )

    print("Default outbound rule removed.")

except ec2.exceptions.ClientError:

    print(
        "Default outbound rule already removed "
        "or not found."
    )


# =========================================================
# ADD MYSQL INBOUND FROM WEBSG
# =========================================================

print("\nConfiguring MySQL inbound rule...")

try:

    ec2.authorize_security_group_ingress(

        GroupId=rds_sg_id,

        IpPermissions=[
            {
                "IpProtocol": "tcp",

                "FromPort": DB_PORT,

                "ToPort": DB_PORT,

                "UserIdGroupPairs": [
                    {
                        "GroupId": WEB_SG_ID,

                        "Description": (
                            "Allow MySQL from Web/App Tier"
                        )
                    }
                ]
            }
        ]
    )

    print(
        "MySQL 3306 access from websG "
        "added successfully."
    )

except ec2.exceptions.ClientError as error:

    if "InvalidPermission.Duplicate" in str(error):

        print(
            "MySQL rule already exists."
        )

    else:

        raise


# =========================================================
# ADD OUTBOUND TO WEB SG ONLY


print("\nConfiguring outbound MySQL rule...")

try:

    ec2.authorize_security_group_egress(

        GroupId=rds_sg_id,

        IpPermissions=[
            {
                "IpProtocol": "tcp",

                "FromPort": DB_PORT,

                "ToPort": DB_PORT,

                "UserIdGroupPairs": [
                    {
                        "GroupId": WEB_SG_ID,

                        "Description": (
                            "Allow MySQL responses to Web/App Tier"
                        )
                    }
                ]
            }
        ]
    )

    print(
        "Outbound MySQL rule added successfully."
    )

except ec2.exceptions.ClientError as error:

    if "InvalidPermission.Duplicate" in str(error):

        print(
            "Outbound MySQL rule already exists."
        )

    else:

        raise


# =========================================================
# GET FINAL SECURITY GROUP


final_response = ec2.describe_security_groups(
    GroupIds=[rds_sg_id]
)

rds_sg = final_response["SecurityGroups"][0]




print("\n")
print("=" * 65)
print("          RDS SECURITY GROUP COMPLETED")
print("=" * 65)

print(f"\nName        : {rds_sg['GroupName']}")

print(f"Group ID    : {rds_sg['GroupId']}")

print(f"VPC ID      : {rds_sg['VpcId']}")

print("\nInbound:")

print(
    f"  MySQL TCP {DB_PORT} "
    f"from websG ({WEB_SG_ID})"
)

print("\nOutbound:")

print(
    f"  MySQL TCP {DB_PORT} "
    f"to websG ({WEB_SG_ID})"
)

print("\n")
print("=" * 65)
print("             RDSSG READY")
print("=" * 65)