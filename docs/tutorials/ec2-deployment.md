# EC2 Deployment with IAM Instance Profile

This tutorial describes how to deploy Fluentia on an Amazon EC2 instance using Docker. The instance uses an IAM role (instance profile) so that AWS Bedrock credentials rotate automatically without manual intervention.

## Prerequisites

- Access to the AWS Management Console with permissions to create IAM roles, EC2 instances, and security groups
- Amazon Bedrock enabled in your AWS region (this tutorial uses `us-east-1`)
- A Google Gemini API key (for the Google provider)
- An SSH key pair (or willingness to create one)
- The Fluentia repository URL

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│  EC2 Instance (Ubuntu 24.04)                 │
│  IAM Role: fluentia-ec2-role                  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  Docker Container (--network host)     │  │
│  │  Fluentia app on port 8000              │  │
│  │  Reads credentials from IMDS via role  │  │
│  └────────────────────────────────────────┘  │
│                                              │
└──────────────────────────────────────────────┘
         │
         ▼
   Security Group: fluentia-sg
   Inbound: TCP 22 (SSH), TCP 8000 (App)
```

The EC2 instance has an IAM role attached via an instance profile. The AWS SDK inside the container resolves credentials from the EC2 Instance Metadata Service (IMDS), which handles credential rotation transparently.

## Step 1: Create an IAM Role

1. Open the **IAM** console.
2. Go to **Roles** > **Create role**.
3. Select **AWS service** as the trusted entity type.
4. Select **EC2** as the use case. Click **Next**.
5. Attach the following managed policy:
   - `AmazonBedrockFullAccess`

   For a more restrictive policy, create a custom policy with only the `bedrock:InvokeModelWithResponseStream` action on the specific model resource you use.
6. Click **Next**.
7. Name the role `fluentia-ec2-role`. Click **Create role**.

AWS automatically creates an instance profile with the same name when you create a role through the console with EC2 as the use case.

## Step 2: Create a Security Group

1. Open the **EC2** console. Select the region where Bedrock is enabled (e.g., `us-east-1`).
2. Go to **Security Groups** > **Create security group**.
3. Configure:
   - **Name**: `fluentia-sg`
   - **Description**: `Allow SSH and Fluentia app access`
   - **VPC**: Select your default VPC (or the VPC where you want the instance)
4. Add **inbound rules**:

   | Type       | Port | Source        | Description          |
   |------------|------|---------------|----------------------|
   | SSH        | 22   | My IP         | SSH access           |
   | Custom TCP | 8000 | My IP         | Fluentia web UI       |

   Using **My IP** restricts access to your current public IP address. For team access, use a specific CIDR range instead.
5. Leave outbound rules as default (allow all). The instance needs outbound access to pull Docker images, clone the repository, and reach AWS Bedrock endpoints.
6. Click **Create security group**.

## Step 3: Create a Key Pair

Skip this step if you already have an EC2 key pair in the target region.

1. In the EC2 console, go to **Key Pairs** > **Create key pair**.
2. Configure:
   - **Name**: `fluentia-key`
   - **Type**: RSA
   - **Format**: `.pem`
3. Click **Create key pair**. The browser downloads `fluentia-key.pem`.
4. Restrict permissions on the downloaded key:

```bash
chmod 400 fluentia-key.pem
```

## Step 4: Launch the EC2 Instance

1. In the EC2 console, click **Launch instances**.
2. Configure:
   - **Name**: `fluentia-server`
   - **AMI**: Ubuntu Server 24.04 LTS (HVM), SSD Volume Type (64-bit x86)
   - **Instance type**: `t3.medium` (2 vCPUs, 4 GB RAM — sufficient for running the Docker build and serving the app)
   - **Key pair**: Select `fluentia-key` (or your existing key pair)
3. Under **Network settings**, click **Edit**:
   - **Auto-assign public IP**: Enable (required to access the instance via SSH and the web UI; some subnets disable this by default)
   - **Security group**: Select existing > `fluentia-sg`
4. Under **Advanced details**:
   - **IAM instance profile**: Select `fluentia-ec2-role`
   - **Metadata version**: Ensure IMDSv2 is set to **Optional** or **Required** (both work; if required, the Docker container needs the hop limit set to 2 — see below)
5. Leave storage as default (8 GB gp3 is sufficient).
6. Click **Launch instance**.
7. Wait for the instance to reach the **Running** state and pass status checks.

### IMDSv2 Hop Limit

If you set metadata version to **Required** (IMDSv2 only), increase the hop limit to 2 so the Docker container can reach the metadata service:

1. Select the instance in the EC2 console.
2. Go to **Actions** > **Instance settings** > **Modify instance metadata options**.
3. Set **Metadata response hop limit** to `2`.

This is necessary because Docker's network bridge adds one network hop. If you use `--network host` when running the container (as this tutorial does), the default hop limit of 1 is sufficient.

## Step 5: Connect via SSH

Find the instance's **Public IPv4 address** in the EC2 console.

```bash
ssh -i fluentia-key.pem ubuntu@<PUBLIC_IP>
```

If you get a "Permission denied" error, verify the key file permissions (`chmod 400`) and that you are using the correct username (`ubuntu` for Ubuntu AMIs).

## Step 6: Install Docker

On the EC2 instance, install Docker using the official convenience script:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and back in for the group membership to take effect:

```bash
exit
```

Then reconnect:

```bash
ssh -i fluentia-key.pem ubuntu@<PUBLIC_IP>
```

Verify Docker is working:

```bash
docker run --rm hello-world
```

## Step 7: Install uv and Clone the Repository

Install uv (not strictly required for the Docker-based deployment, but useful for running commands directly):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

Clone the repository:

```bash
git clone <REPOSITORY_URL>
cd <REPOSITORY_DIRECTORY>
```

Replace `<REPOSITORY_URL>` and `<REPOSITORY_DIRECTORY>` with the actual repository URL and directory name.

## Step 8: Build the Docker Image

From the repository root:

```bash
docker build -t fluentia .
```

The multi-stage build installs dependencies, builds a Python wheel, and produces a minimal production image. This takes a few minutes on the first run.

## Step 9: Run the Container

Export the Google Gemini API key in your terminal session:

```bash
export GOOGLE_API_KEY="your-google-api-key"
```

Run the container with `--network host` so it can access the EC2 Instance Metadata Service for AWS credentials:

```bash
docker run -d \
  --name fluentia \
  --network host \
  --restart unless-stopped \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  -e BEDROCK_REGION=us-east-1 \
  -e FLUENTIA_LOG_LEVEL=INFO \
  fluentia
```

The `--network host` flag is important: it allows the container to reach the EC2 metadata endpoint (`169.254.169.254`) to resolve IAM role credentials. It also means the container binds directly to port 8000 on the host — no port mapping needed.

Verify the container is running:

```bash
docker ps
```

Check the logs:

```bash
docker logs -f fluentia
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

## Step 10: Access the Web UI

Open a browser and navigate to:

```
http://<PUBLIC_IP>:8000
```

Use the public IP address of your EC2 instance. Select the **Bedrock** provider to use AWS credentials from the instance role, or **Google Gemini** to use the API key you exported.

### Verify Health

```bash
curl http://<PUBLIC_IP>:8000/health
curl http://<PUBLIC_IP>:8000/ready
```

## Managing the Container

```bash
# Stop
docker stop fluentia

# Start again
docker start fluentia

# View logs
docker logs -f fluentia

# Remove and recreate
docker rm -f fluentia
# Then re-run the docker run command from Step 9
```

## Troubleshooting

### Bedrock Returns "Credentials Not Found"

1. Verify the IAM role is attached to the instance:
   ```bash
   curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
   ```
   This should return the role name (`fluentia-ec2-role`). If it returns a 404, the instance profile is not attached.

2. Verify the container can reach the metadata service:
   ```bash
   docker exec fluentia curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
   ```
   If this fails, ensure you are using `--network host`.

3. Verify the application logs show `Using SigV4 authentication with chained credential resolver for Bedrock` at startup.

### Cannot Connect to Port 8000

1. Check that the security group allows inbound TCP 8000 from your IP.
2. Your public IP may have changed since you created the security group rule. Update the rule with your current IP.
3. Verify the container is running: `docker ps`.

### Docker Build Fails

If the build runs out of memory on a small instance, use a larger instance type (`t3.large` or above) or add swap:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### SSH Connection Refused

1. Verify the instance is running and has passed status checks in the EC2 console.
2. Confirm the security group allows SSH (port 22) from your current IP.
3. Check you are using the correct key pair and username (`ubuntu` for Ubuntu AMIs).

## Security Considerations

- The security group rules in this tutorial restrict access to your IP address. For production use, consider placing the instance behind a load balancer with HTTPS termination.
- The application serves over HTTP (not HTTPS). Do not expose port 8000 to the public internet for production workloads without a TLS-terminating reverse proxy.
- The `AmazonBedrockFullAccess` policy is broad. For production, scope the IAM policy to the specific Bedrock actions and model resources the application needs.
- The Google API key is passed as an environment variable and is visible in the container's environment. For production, consider using AWS Secrets Manager or Parameter Store.
