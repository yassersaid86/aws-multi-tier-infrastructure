# AWS Multi-Tier Infrastructure

A production-style, highly available multi-tier web infrastructure built on AWS and automated using **Python & Boto3**.

The project demonstrates how to design and deploy a secure, scalable, and highly available web application architecture using multiple AWS services across Availability Zones.

## 🏗️ Architecture

```text
                         Internet
                            │
                            ▼
                  ┌──────────────────┐
                  │   Application     │
                  │   Load Balancer   │
                  └────────┬─────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
        Public Subnet A           Public Subnet B
          us-east-1a                us-east-1b
              │                         │
              │       ALB              │
              └────────────┬────────────┘
                           │
                  ┌────────┴────────┐
                  │                 │
                  ▼                 ▼
            Private Subnet A   Private Subnet B
              us-east-1a         us-east-1b
                  │                 │
               EC2/App           EC2/App
                  │                 │
                NAT A             NAT B
                  │                 │
                  └────────┬────────┘
                           │
                           ▼
                    Multi-AZ RDS
                       MySQL
```

## ☁️ AWS Services

The project uses the following AWS services:

* **Amazon VPC** — Custom network architecture
* **Amazon EC2** — Application/Web servers
* **Application Load Balancer** — Traffic distribution
* **Auto Scaling Group** — Automatic scaling and instance replacement
* **Amazon RDS** — Managed MySQL database
* **NAT Gateway** — Secure outbound internet access from private subnets
* **Internet Gateway** — Internet connectivity for public resources
* **Elastic IP** — Static public IPs for NAT Gateways
* **Security Groups** — Network-level access control
* **AWS IAM** — Identity and access management
* **AWS Secrets Manager** — Managed RDS master password
* **Amazon EBS** — Encrypted EC2 storage

## 🌐 Network Architecture

The project uses a custom VPC:

```text
VPC: 10.0.0.0/16
```

### Public Subnets

| Subnet   | CIDR         | Availability Zone |
| -------- | ------------ | ----------------- |
| Public A | 10.0.10.0/24 | us-east-1a        |
| Public B | 10.0.20.0/24 | us-east-1b        |

Public subnets are used for internet-facing infrastructure such as the Application Load Balancer.

### Private Subnets

| Subnet    | CIDR          | Availability Zone |
| --------- | ------------- | ----------------- |
| Private A | 10.0.100.0/24 | us-east-1a        |
| Private B | 10.0.200.0/24 | us-east-1b        |

Application servers are deployed in private subnets and are not directly accessible from the public internet.

## 🔄 NAT Gateway

Each Availability Zone contains its own NAT Gateway:

```text
Private Subnet A → NAT Gateway A → Internet Gateway

Private Subnet B → NAT Gateway B → Internet Gateway
```

Using one NAT Gateway per Availability Zone improves availability and avoids relying on a single AZ.

## 🖥️ EC2 Application Tier

The application tier runs on Amazon EC2 instances inside the private subnets.

The EC2 instances use:

* Amazon Linux
* Apache HTTP Server
* EBS-backed storage
* Encrypted EBS volumes
* Security Group restrictions
* User Data for automated web-server configuration

The instances are registered with the Application Load Balancer target group.

## ⚖️ Application Load Balancer

The Application Load Balancer is deployed across both public subnets.

Traffic flow:

```text
Internet
   │
   ▼
Application Load Balancer
   │
   ├── EC2 Instance 1
   │
   └── EC2 Instance 2
```

The ALB performs health checks on the application servers and sends traffic only to healthy targets.

## 📈 Auto Scaling

The project uses an Auto Scaling Group with:

```text
Minimum Instances: 2
Desired Instances: 2
Maximum Instances: 4
CPU Target: 50%
```

The Auto Scaling Group provides:

* Automatic instance replacement
* High availability
* Horizontal scaling
* Integration with the Application Load Balancer
* CPU-based target tracking

## 🗄️ Database Layer

The project uses **Amazon RDS for MySQL**.

Configuration includes:

* MySQL
* Multi-AZ deployment
* Private access
* Encryption at rest
* Private subnet deployment
* Security Group restricted access
* AWS Secrets Manager for the master password

The database is not publicly accessible.

## 🔐 Security

Security is implemented using multiple layers.

### Application Security Group

The web/application security group allows:

```text
HTTP 80  → Only from ALB Security Group
HTTPS 443 → Only from ALB Security Group
SSH 22   → From VPC CIDR
```

### Load Balancer Security Group

The ALB security group allows:

```text
HTTP 80 → Internet
```

and forwards application traffic to the application security group.

### Database Security Group

The RDS security group allows MySQL traffic:

```text
3306 → Only from the application/web security group
```

This prevents direct public access to the database.

## 🐍 Infrastructure Automation

The infrastructure is automated using:

```text
Python
Boto3
AWS SDK
```

Each infrastructure component is organized into a separate Python script.

### Project Structure

```text
aws-multi-tier-infrastructure/
│
├── vpc.py
├── subnet.py
├── internet_gateway.py
├── public_route_table.py
├── private_route_tables.py
├── nat_gateways.py
├── security_groups.py
├── ec2.py
├── target_group.py
├── load_balancer.py
├── listener.py
├── auto_scaling.py
├── rds_security_group.py
├── rds_subnet_group.py
├── rds.py
├── test_connection.py
├── final_test.py
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Requirements

Before running the project, install:

* Python 3.x
* AWS CLI
* AWS account
* Boto3
* Git

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## 🔑 AWS Configuration

The project uses an AWS CLI profile named:

```text
acc-admin
```

and the AWS region:

```text
us-east-1
```

Configure your own AWS credentials locally.

**Never commit AWS access keys, secret keys, passwords, `.pem` files, or other credentials to GitHub.**

The repository includes a `.gitignore` file to prevent sensitive and unnecessary files from being committed.

## 🚀 Deployment

Run the infrastructure scripts in dependency order.

```text
1. vpc.py
2. subnet.py
3. internet_gateway.py
4. public_route_table.py
5. private_route_tables.py
6. nat_gateways.py
7. security_groups.py
8. ec2.py
9. target_group.py
10. load_balancer.py
11. listener.py
12. auto_scaling.py
13. rds_security_group.py
14. rds_subnet_group.py
15. rds.py
16. final_test.py
```

The scripts create and configure the required AWS resources using Boto3.

## 🧪 Testing

The project includes:

### `test_connection.py`

Tests the AWS account connection using AWS STS.

### `final_test.py`

Validates the main infrastructure components, including:

* Target Group
* Target Health
* Application Load Balancer
* ALB Listener
* Auto Scaling Group
* RDS
* Multi-AZ configuration
* Encryption
* Public accessibility

## 🎯 Project Goals

This project was built to demonstrate practical experience with:

* AWS Cloud Architecture
* VPC Networking
* Multi-AZ Infrastructure
* Infrastructure Automation
* Python & Boto3
* Load Balancing
* Auto Scaling
* EC2
* NAT Gateways
* Amazon RDS
* Network Security
* Cloud Infrastructure Design

## 📌 Key Features

* ✅ Custom VPC
* ✅ Multi-AZ architecture
* ✅ Public and private subnets
* ✅ Internet Gateway
* ✅ NAT Gateway per AZ
* ✅ Private application servers
* ✅ Application Load Balancer
* ✅ Auto Scaling
* ✅ Health checks
* ✅ Multi-AZ MySQL RDS
* ✅ Encrypted storage
* ✅ Security Group isolation
* ✅ AWS Secrets Manager
* ✅ Infrastructure automation with Python/Boto3

## 👨‍💻 Author

**Yasser Said**

Backend Developer | Node.js | AWS | Python

GitHub: [yassersaid86](https://github.com/yassersaid86)
