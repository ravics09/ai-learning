###############################################################################
# terraform_gpu_infra.tf
# ------------------------------------------------------------------------------
# Illustrative Terraform for a cost-aware GPU inference stack on AWS.
#
# WHY this file exists (interview points it demonstrates):
#   1. REMOTE STATE with locking  -> safe team collaboration, no state corruption.
#   2. GPU nodes on SPOT           -> ~60-90% cheaper for fault-tolerant inference.
#   3. AUTOSCALING node group      -> pay for capacity you actually use.
#   4. SECRETS via Secrets Manager -> never hardcode keys / never in state as plaintext.
#   5. PRIVATE networking + IAM    -> least privilege, no public internet for model calls.
#
# This is a teaching scaffold: simplified for readability. Pin versions and add
# modules/tags/policy-as-code in real projects.
###############################################################################

terraform {
  required_version = ">= 1.9" # 1.9+ has better GPU provider support + ephemeral values

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  # WHY remote state + DynamoDB lock: shared, versioned state; the lock prevents two
  # engineers/CI runs from applying at once and corrupting state. Separate this backend
  # per environment (dev/stage/prod) to bound blast radius.
  backend "s3" {
    bucket         = "my-org-tfstate"
    key            = "ai/gpu-infra/prod.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf-locks"
    encrypt        = true # state encrypted at rest with KMS
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cluster_name" {
  type    = string
  default = "llm-inference"
}

###############################################################################
# EKS cluster (control plane). Node groups below run the GPU workloads.
###############################################################################
resource "aws_eks_cluster" "this" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.31"

  vpc_config {
    subnet_ids              = var.private_subnet_ids # WHY private: nodes not exposed to internet
    endpoint_public_access  = false                  # API server reachable only privately
    endpoint_private_access = true
  }
}

variable "private_subnet_ids" {
  type    = list(string)
  default = ["subnet-aaaa", "subnet-bbbb"] # illustrative; span 2+ AZs for HA
}

###############################################################################
# GPU node group on SPOT with autoscaling.
# WHY spot: inference replicas are stateless behind a queue/LB, so a reclaimed node
# just drains and reschedules -> huge savings with minimal risk.
###############################################################################
resource "aws_eks_node_group" "gpu_spot" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "gpu-spot"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnet_ids

  # g6 = L4 GPUs: cost-efficient for small/mid model inference. Multiple types reduce
  # the chance ALL your spot capacity gets reclaimed at the same time.
  instance_types = ["g6.xlarge", "g6.2xlarge"]
  capacity_type  = "SPOT"

  scaling_config {
    desired_size = 2
    min_size     = 0 # scale-to-zero when idle (with a separate always-on baseline group)
    max_size     = 10
  }

  # Taint so ONLY GPU workloads land here; CPU glue stays on cheaper nodes.
  taint {
    key    = "nvidia.com/gpu"
    value  = "present"
    effect = "NO_SCHEDULE"
  }

  labels = { workload = "gpu-inference" }
}

# In production, ALSO add Karpenter for faster, bin-packed, multi-type GPU provisioning.

###############################################################################
# IAM roles (least privilege). Real policies would be scoped tightly, not shown fully.
###############################################################################
resource "aws_iam_role" "eks_cluster" {
  name = "${var.cluster_name}-cluster"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "eks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role" "node" {
  name = "${var.cluster_name}-node"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

###############################################################################
# Secrets: reference a manager, DO NOT hardcode. WHY: values in .tf or state can leak.
# Terraform reads the secret at apply time; mark outputs sensitive. Even better in
# 1.9+: use ephemeral resources so the value never lands in state at all.
###############################################################################
data "aws_secretsmanager_secret" "model_api_key" {
  name = "prod/llm/model-api-key" # created & rotated outside TF, in Secrets Manager
}

data "aws_secretsmanager_secret_version" "model_api_key" {
  secret_id = data.aws_secretsmanager_secret.model_api_key.id
}

output "cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

# NOTE: we deliberately do NOT output the secret value. Secrets are injected into pods at
# runtime via a CSI driver / External Secrets Operator, not surfaced as TF outputs.
