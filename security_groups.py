import boto3

# ==========================================
# AWS Session
# ==========================================

session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

ec2 = session.client("ec2")


# ==========================================
# Existing Resources
# ==========================================

VPC_ID = "vpc-0a43899641820473c"

VPC_CIDR = "10.0.0.0/16"


# ==========================================
# Helper Function
# ==========================================

def get_security_group_by_name(group_name):

    response = ec2.describe_security_groups(
        Filters=[
            {
                "Name": "group-name",
                "Values": [group_name]
            },
            {
                "Name": "vpc-id",
                "Values": [VPC_ID]
            }
        ]
    )

    if response["SecurityGroups"]:
        return response["SecurityGroups"][0]["GroupId"]

    return None


# ==========================================
# 1. Create ALB Security Group
# ==========================================

print("Checking ALBSG...")

alb_sg_id = get_security_group_by_name("ALBSG")

if alb_sg_id:

    print("ALBSG already exists.")
    print(f"ALBSG ID: {alb_sg_id}")

else:

    print("Creating ALBSG...")

    response = ec2.create_security_group(
        GroupName="ALBSG",
        Description="Security Group for Application Load Balancer",
        VpcId=VPC_ID,
        TagSpecifications=[
            {
                "ResourceType": "security-group",
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": "ALBSG"
                    }
                ]
            }
        ]
    )

    alb_sg_id = response["GroupId"]

    print("ALBSG created successfully!")
    print(f"ALBSG ID: {alb_sg_id}")


# ==========================================
# 2. ALBSG Inbound HTTP
# ==========================================

print("\nConfiguring ALBSG inbound rules...")

try:

    ec2.authorize_security_group_ingress(
        GroupId=alb_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                        "Description": "HTTP from Internet"
                    }
                ]
            }
        ]
    )

    print("ALBSG inbound HTTP 80 added.")

except ec2.exceptions.ClientError as e:

    if "InvalidPermission.Duplicate" in str(e):
        print("ALBSG HTTP 80 rule already exists.")
    else:
        raise


# ==========================================
# 3. Configure ALBSG Outbound HTTP
# ==========================================

print("\nConfiguring ALBSG outbound rules...")

# Remove default outbound rule
try:

    ec2.revoke_security_group_egress(
        GroupId=alb_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "-1",
                "FromPort": -1,
                "ToPort": -1,
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0"
                    }
                ]
            }
        ]
    )

    print("Default ALBSG outbound rule removed.")

except ec2.exceptions.ClientError:
    print("Default outbound rule was already removed.")


# ==========================================
# 4. Create WebSG
# ==========================================

print("\nChecking websG...")

web_sg_id = get_security_group_by_name("websG")

if web_sg_id:

    print("websG already exists.")
    print(f"websG ID: {web_sg_id}")

else:

    print("Creating websG...")

    response = ec2.create_security_group(
        GroupName="websG",
        Description="Security Group for Web and Application EC2 instances",
        VpcId=VPC_ID,
        TagSpecifications=[
            {
                "ResourceType": "security-group",
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": "websG"
                    }
                ]
            }
        ]
    )

    web_sg_id = response["GroupId"]

    print("websG created successfully!")
    print(f"websG ID: {web_sg_id}")


# ==========================================
# 5. websG Inbound HTTP from ALBSG
# ==========================================

print("\nConfiguring websG HTTP rule...")

try:

    ec2.authorize_security_group_ingress(
        GroupId=web_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "UserIdGroupPairs": [
                    {
                        "GroupId": alb_sg_id,
                        "Description": "HTTP from ALB"
                    }
                ]
            }
        ]
    )

    print("websG HTTP 80 from ALBSG added.")

except ec2.exceptions.ClientError as e:

    if "InvalidPermission.Duplicate" in str(e):
        print("websG HTTP 80 rule already exists.")
    else:
        raise


# ==========================================
# 6. websG Inbound HTTPS from ALBSG
# ==========================================

print("\nConfiguring websG HTTPS rule...")

try:

    ec2.authorize_security_group_ingress(
        GroupId=web_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 443,
                "ToPort": 443,
                "UserIdGroupPairs": [
                    {
                        "GroupId": alb_sg_id,
                        "Description": "HTTPS from ALB"
                    }
                ]
            }
        ]
    )

    print("websG HTTPS 443 from ALBSG added.")

except ec2.exceptions.ClientError as e:

    if "InvalidPermission.Duplicate" in str(e):
        print("websG HTTPS 443 rule already exists.")
    else:
        raise


# ==========================================
# 7. websG SSH
# ==========================================

print("\nConfiguring websG SSH rule...")

try:

    ec2.authorize_security_group_ingress(
        GroupId=web_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [
                    {
                        "CidrIp": VPC_CIDR,
                        "Description": "SSH from inside VPC"
                    }
                ]
            }
        ]
    )

    print("websG SSH 22 rule added.")

except ec2.exceptions.ClientError as e:

    if "InvalidPermission.Duplicate" in str(e):
        print("websG SSH 22 rule already exists.")
    else:
        raise


# ==========================================
# 8. websG Outbound HTTP + HTTPS
# ==========================================

print("\nConfiguring websG outbound rules...")

# Remove default outbound rule
try:

    ec2.revoke_security_group_egress(
        GroupId=web_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "-1",
                "FromPort": -1,
                "ToPort": -1,
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0"
                    }
                ]
            }
        ]
    )

    print("Default websG outbound rule removed.")

except ec2.exceptions.ClientError:
    print("Default websG outbound rule was already removed.")


# HTTP + HTTPS outbound
try:

    ec2.authorize_security_group_egress(
        GroupId=web_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                        "Description": "HTTP outbound through NAT"
                    }
                ]
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 443,
                "ToPort": 443,
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                        "Description": "HTTPS outbound through NAT"
                    }
                ]
            }
        ]
    )

    print("websG outbound HTTP 80 added.")
    print("websG outbound HTTPS 443 added.")

except ec2.exceptions.ClientError as e:

    if "InvalidPermission.Duplicate" in str(e):
        print("websG outbound rules already exist.")
    else:
        raise


# ==========================================
# 9. ALBSG Outbound HTTP to websG
# ==========================================

print("\nConfiguring ALBSG outbound HTTP to websG...")

try:

    ec2.authorize_security_group_egress(
        GroupId=alb_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "UserIdGroupPairs": [
                    {
                        "GroupId": web_sg_id,
                        "Description": "HTTP to Web/App instances"
                    }
                ]
            }
        ]
    )

    print("ALBSG outbound HTTP to websG added.")

except ec2.exceptions.ClientError as e:

    if "InvalidPermission.Duplicate" in str(e):
        print("ALBSG outbound HTTP rule already exists.")
    else:
        raise


# ==========================================
# Final
# ==========================================

print("\n================================")
print("SECURITY GROUPS CONFIGURED")
print("================================")

print(f"ALBSG ID : {alb_sg_id}")
print(f"websG ID : {web_sg_id}")

print("\nALBSG:")
print("  Inbound  : HTTP 80 from Internet")
print("  Outbound : HTTP 80 to websG")

print("\nwebsG:")
print("  Inbound  : HTTP 80 from ALBSG")
print("  Inbound  : HTTPS 443 from ALBSG")
print("  Inbound  : SSH 22 from VPC")
print("  Outbound : HTTP 80 to Internet")
print("  Outbound : HTTPS 443 to Internet")

print("================================")