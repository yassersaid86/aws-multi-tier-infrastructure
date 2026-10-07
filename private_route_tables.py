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

PRIVATE_SUBNET_A_ID = "subnet-07a027f8b854f114a"
PRIVATE_SUBNET_B_ID = "subnet-0de4f1e9875766ba1"

NAT_GATEWAY_A_ID = "nat-00b1e8395f34bc4a5"
NAT_GATEWAY_B_ID = "nat-00e49c771cd9ec60f"


# ==========================================
# 1. Create Private Route Table A
# ==========================================

print("Creating Private Route Table A...")

route_table_a_response = ec2.create_route_table(
    VpcId=VPC_ID,
    TagSpecifications=[
        {
            "ResourceType": "route-table",
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "Private-Route-Table-A"
                }
            ]
        }
    ]
)

private_route_table_a_id = (
    route_table_a_response["RouteTable"]["RouteTableId"]
)

print("Private Route Table A created successfully!")
print(f"Route Table A ID: {private_route_table_a_id}")


# ==========================================
# 2. Add Default Route to NAT Gateway A
# ==========================================

print("\nAdding NAT Gateway A route...")

ec2.create_route(
    RouteTableId=private_route_table_a_id,
    DestinationCidrBlock="0.0.0.0/0",
    NatGatewayId=NAT_GATEWAY_A_ID
)

print("Default route added successfully!")
print("0.0.0.0/0 -> NAT Gateway A")


# ==========================================
# 3. Associate Private Subnet A
# ==========================================

print("\nAssociating Private Subnet A...")

association_a = ec2.associate_route_table(
    RouteTableId=private_route_table_a_id,
    SubnetId=PRIVATE_SUBNET_A_ID
)

print("Private Subnet A associated successfully!")
print(f"Association ID: {association_a['AssociationId']}")


# ==========================================
# 4. Create Private Route Table B
# ==========================================

print("\nCreating Private Route Table B...")

route_table_b_response = ec2.create_route_table(
    VpcId=VPC_ID,
    TagSpecifications=[
        {
            "ResourceType": "route-table",
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "Private-Route-Table-B"
                }
            ]
        }
    ]
)

private_route_table_b_id = (
    route_table_b_response["RouteTable"]["RouteTableId"]
)

print("Private Route Table B created successfully!")
print(f"Route Table B ID: {private_route_table_b_id}")


# ==========================================
# 5. Add Default Route to NAT Gateway B
# ==========================================

print("\nAdding NAT Gateway B route...")

ec2.create_route(
    RouteTableId=private_route_table_b_id,
    DestinationCidrBlock="0.0.0.0/0",
    NatGatewayId=NAT_GATEWAY_B_ID
)

print("Default route added successfully!")
print("0.0.0.0/0 -> NAT Gateway B")


# ==========================================
# 6. Associate Private Subnet B
# ==========================================

print("\nAssociating Private Subnet B...")

association_b = ec2.associate_route_table(
    RouteTableId=private_route_table_b_id,
    SubnetId=PRIVATE_SUBNET_B_ID
)

print("Private Subnet B associated successfully!")
print(f"Association ID: {association_b['AssociationId']}")


# ==========================================
# Final
# ==========================================

print("\n================================")
print("PRIVATE ROUTE TABLES COMPLETED")
print("================================")

print(f"Private Route Table A: {private_route_table_a_id}")
print(f"Private Route Table B: {private_route_table_b_id}")

print("Private Subnet A -> NAT Gateway A")
print("Private Subnet B -> NAT Gateway B")

print("================================")