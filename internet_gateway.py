import boto3

session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

ec2 = session.client("ec2")

VPC_ID = "vpc-0a43899641820473c"

# ==========================================
# 5. Create Internet Gateway
# ==========================================

igw_response = ec2.create_internet_gateway(
    TagSpecifications=[
        {
            "ResourceType": "internet-gateway",
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "Yasser-IGW"
                }
            ]
        }
    ]
)

igw_id = igw_response["InternetGateway"]["InternetGatewayId"]

print(f"Internet Gateway created: {igw_id}")


# ==========================================
# 6. Attach Internet Gateway to VPC
# ==========================================

ec2.attach_internet_gateway(
    InternetGatewayId=igw_id,
    VpcId=VPC_ID
)

print(f"Internet Gateway {igw_id} attached to VPC {VPC_ID}")