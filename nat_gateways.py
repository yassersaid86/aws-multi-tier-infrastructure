import boto3
import time

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

PUBLIC_SUBNET_A_ID = "subnet-0e5123dbb4a75933a"

PUBLIC_SUBNET_B_ID = "subnet-076b612bcaadebf07"


# ==========================================
# 1. Allocate Elastic IP for NAT Gateway A
# ==========================================

print("Allocating Elastic IP for NAT Gateway A...")

eip_a = ec2.allocate_address(
    Domain="vpc",
    TagSpecifications=[
        {
            "ResourceType": "elastic-ip",
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "NAT-EIP-A"
                }
            ]
        }
    ]
)

allocation_id_a = eip_a["AllocationId"]
public_ip_a = eip_a["PublicIp"]

print("Elastic IP A allocated successfully!")
print(f"Allocation ID: {allocation_id_a}")
print(f"Public IP: {public_ip_a}")


# ==========================================
# 2. Allocate Elastic IP for NAT Gateway B


print("\nAllocating Elastic IP for NAT Gateway B...")

eip_b = ec2.allocate_address(
    Domain="vpc",
    TagSpecifications=[
        {
            "ResourceType": "elastic-ip",
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "NAT-EIP-B"
                }
            ]
        }
    ]
)

allocation_id_b = eip_b["AllocationId"]
public_ip_b = eip_b["PublicIp"]

print("Elastic IP B allocated successfully!")
print(f"Allocation ID: {allocation_id_b}")
print(f"Public IP: {public_ip_b}")


# ==========================================
# 3. Create NAT Gateway A


print("\nCreating NAT Gateway A...")

nat_a_response = ec2.create_nat_gateway(
    SubnetId=PUBLIC_SUBNET_A_ID,
    AllocationId=allocation_id_a,
    TagSpecifications=[
        {
            "ResourceType": "natgateway",
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "NAT-Gateway-A"
                }
            ]
        }
    ]
)

nat_a_id = nat_a_response["NatGateway"]["NatGatewayId"]

print("NAT Gateway A created!")
print(f"NAT Gateway A ID: {nat_a_id}")


# ==========================================
# 4. Create NAT Gateway B


print("\nCreating NAT Gateway B...")

nat_b_response = ec2.create_nat_gateway(
    SubnetId=PUBLIC_SUBNET_B_ID,
    AllocationId=allocation_id_b,
    TagSpecifications=[
        {
            "ResourceType": "natgateway",
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "NAT-Gateway-B"
                }
            ]
        }
    ]
)

nat_b_id = nat_b_response["NatGateway"]["NatGatewayId"]

print("NAT Gateway B created!")
print(f"NAT Gateway B ID: {nat_b_id}")




print("\nWaiting for NAT Gateway A to become available...")

while True:

    response = ec2.describe_nat_gateways(
        NatGatewayIds=[nat_a_id]
    )

    state = response["NatGateways"][0]["State"]

    print(f"NAT Gateway A state: {state}")

    if state == "available":
        break

    if state == "failed":
        raise Exception("NAT Gateway A creation failed!")

    time.sleep(15)




print("\nWaiting for NAT Gateway B to become available...")

while True:

    response = ec2.describe_nat_gateways(
        NatGatewayIds=[nat_b_id]
    )

    state = response["NatGateways"][0]["State"]

    print(f"NAT Gateway B state: {state}")

    if state == "available":
        break

    if state == "failed":
        raise Exception("NAT Gateway B creation failed!")

    time.sleep(15)




print("\n================================")
print("NAT GATEWAYS CREATED SUCCESSFULLY")
print("================================")

print(f"NAT Gateway A: {nat_a_id}")
print(f"NAT Gateway B: {nat_b_id}")

print(f"NAT EIP A: {public_ip_a}")
print(f"NAT EIP B: {public_ip_b}")

print("================================")