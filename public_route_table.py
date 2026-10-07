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

IGW_ID = "igw-0971a6b6622fa79af"

PUBLIC_SUBNET_A_ID = "subnet-0e5123dbb4a75933a"

PUBLIC_SUBNET_B_ID = "subnet-076b612bcaadebf07"


# ==========================================
# 1. Create Public Route Table
# ==========================================

print("Creating Public Route Table...")

route_table_response = ec2.create_route_table(
    VpcId=VPC_ID,
    TagSpecifications=[
        {
            "ResourceType": "route-table",
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "Public-Route-Table"
                }
            ]
        }
    ]
)

route_table_id = route_table_response["RouteTable"]["RouteTableId"]

print(f"Public Route Table created successfully!")
print(f"Route Table ID: {route_table_id}")


# ==========================================
# 2. Add Default Route to Internet Gateway
# ==========================================

print("\nAdding Internet Gateway route...")

ec2.create_route(
    RouteTableId=route_table_id,
    DestinationCidrBlock="0.0.0.0/0",
    GatewayId=IGW_ID
)

print("Default route added successfully!")
print("0.0.0.0/0 -> Internet Gateway")


# ==========================================
# 3. Associate Public Subnet A
# ==========================================

print("\nAssociating Public Subnet A...")

association_a = ec2.associate_route_table(
    RouteTableId=route_table_id,
    SubnetId=PUBLIC_SUBNET_A_ID
)

print("Public Subnet A associated successfully!")
print(f"Association ID: {association_a['AssociationId']}")


# ==========================================
# 4. Associate Public Subnet B
# ==========================================

print("\nAssociating Public Subnet B...")

association_b = ec2.associate_route_table(
    RouteTableId=route_table_id,
    SubnetId=PUBLIC_SUBNET_B_ID
)

print("Public Subnet B associated successfully!")
print(f"Association ID: {association_b['AssociationId']}")


# ==========================================
# Final
# ==========================================

print("\n================================")
print("PUBLIC ROUTE TABLE COMPLETED")
print("================================")
print(f"Route Table: {route_table_id}")
print("Public Subnet A: Associated")
print("Public Subnet B: Associated")
print("Internet Gateway: Connected")
print("Default Route: 0.0.0.0/0")
print("================================")