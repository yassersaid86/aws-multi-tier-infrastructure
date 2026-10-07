import boto3

sts = boto3.client("sts")

response = sts.get_caller_identity()

print("================================")
print("AWS CONNECTION SUCCESSFUL")
print("================================")
print("Account ID:", response["Account"])
print("User ARN:", response["Arn"])
print("User ID:", response["UserId"])