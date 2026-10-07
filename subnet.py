import boto3

session = boto3.Session(
    profile_name="acc-admin",
    region_name="us-east-1"
)

ec2 = session.client("ec2")

VPC_ID = "vpc-0a43899641820473c"


subnets = [
    {
        "name": "Public-Subnet-A",
        "cidr": "10.0.10.0/24",
        "az": "us-east-1a",
        "public_ip": True
    },
    {
        "name": "Public-Subnet-B",
        "cidr": "10.0.20.0/24",
        "az": "us-east-1b",
        "public_ip": True
    },
    {
        "name": "Private-Subnet-A",
        "cidr": "10.0.100.0/24",
        "az": "us-east-1a",
        "public_ip": False
    },
    {
        "name": "Private-Subnet-B",
        "cidr": "10.0.200.0/24",
        "az": "us-east-1b",
        "public_ip": False
    }
]


for subnet in subnets:

    print(f"\nChecking {subnet['name']}...")

    response = ec2.describe_subnets(
        Filters=[
            {
                "Name": "vpc-id",
                "Values": [VPC_ID]
            },
            {
                "Name": "tag:Name",
                "Values": [subnet["name"]]
            }
        ]
    )

    existing_subnets = response["Subnets"]

    if existing_subnets:
        subnet_id = existing_subnets[0]["SubnetId"]

        print(f"{subnet['name']} already exists.")
        print("Subnet ID:", subnet_id)

        continue

    print(f"Creating {subnet['name']}...")

    response = ec2.create_subnet(
        VpcId=VPC_ID,
        CidrBlock=subnet["cidr"],
        AvailabilityZone=subnet["az"]
    )

    subnet_id = response["Subnet"]["SubnetId"]

    ec2.create_tags(
        Resources=[subnet_id],
        Tags=[
            {
                "Key": "Name",
                "Value": subnet["name"]
            }
        ]
    )

    ec2.modify_subnet_attribute(
        SubnetId=subnet_id,
        MapPublicIpOnLaunch={
            "Value": subnet["public_ip"]
        }
    )

    print(f"{subnet['name']} created successfully!")
    print("Subnet ID:", subnet_id)
    print("CIDR:", subnet["cidr"])
    print("Availability Zone:", subnet["az"])
    print(
        "Auto-assign Public IP:",
        "Enabled" if subnet["public_ip"] else "Disabled"
    )


print("\n================================")
print("ALL SUBNETS CHECK COMPLETED")
print("================================")