import boto3
session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)
# Connect to EC2 service in US East (N. Virginia)
ec2 = boto3.client("ec2", region_name="us-east-1")

print("Creating VPC...")

response = ec2.create_vpc(
    CidrBlock="10.0.0.0/16"
)

vpc_id = response["Vpc"]["VpcId"]

# Add a Name tag to the VPC
ec2.create_tags(
    Resources=[vpc_id],
    Tags=[
        {
            "Key": "Name",
            "Value": "MultiTier-VPC"
        }
    ]
)

# Enable DNS support
ec2.modify_vpc_attribute(
    VpcId=vpc_id,
    EnableDnsSupport={
        "Value": True
    }
)

# Enable DNS hostnames
ec2.modify_vpc_attribute(
    VpcId=vpc_id,
    EnableDnsHostnames={
        "Value": True
    }
)

print("VPC created successfully!")
print("VPC ID:", vpc_id)