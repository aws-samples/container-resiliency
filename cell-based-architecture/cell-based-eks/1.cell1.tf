# Required for public ECR where Karpenter artifacts are hosted
provider "aws" {
  region = "us-east-1"
  alias  = "virginia"
}

data "aws_ecrpublic_authorization_token" "token" {
  provider = aws.virginia
}

provider "kubernetes" {
  alias                  = "k8s-cell1"
  host                   = module.eks_cell1.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks_cell1.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    # This requires the awscli to be installed locally where Terraform is executed
    args = ["eks", "get-token", "--cluster-name", module.eks_cell1.cluster_name]
  }
}

provider "helm" {
  alias = "helm-cell1"
  kubernetes {
    host                   = module.eks_cell1.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks_cell1.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      # This requires the awscli to be installed locally where Terraform is executed
      args = ["eks", "get-token", "--cluster-name", module.eks_cell1.cluster_name]
    }
  }
}

locals {
  cell1_name = format("%s-%s", local.name, "az1")
}

################################################################################
# Cluster
################################################################################

module "eks_cell1" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.11"

  providers = {
    kubernetes = kubernetes.k8s-cell1
  }

  cluster_name                   = local.cell1_name
  cluster_version                = "1.30"
  cluster_endpoint_public_access = true
  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    cell1 = {
      instance_types = ["m5.large"]

      min_size     = 1
      max_size     = 5
      desired_size = 2

      subnet_ids = [module.vpc.private_subnets[0]]
    }
  }

  tags = merge(local.tags, {
    # NOTE - if creating multiple security groups with this module, only tag the
    # security group that Karpenter should utilize with the following tag
    # (i.e. - at most, only one security group should have this tag in your account)
    "karpenter.sh/discovery" = local.cell1_name
  })
}

################################################################################
# EKS Blueprints Addons
################################################################################

module "eks_blueprints_addons_cell1" {
  source  = "aws-ia/eks-blueprints-addons/aws"
  version = "~> 1.16"

  providers = {
    helm       = helm.helm-cell1
    kubernetes = kubernetes.k8s-cell1
  }

  cluster_name      = module.eks_cell1.cluster_name
  cluster_endpoint  = module.eks_cell1.cluster_endpoint
  cluster_version   = module.eks_cell1.cluster_version
  oidc_provider_arn = module.eks_cell1.oidc_provider_arn

  # We want to wait for the EKS Managed Nodegroups to be deployed first
  create_delay_dependencies = [for group in module.eks_cell1.eks_managed_node_groups : group.node_group_arn]

  eks_addons = {
    coredns    = {}
    vpc-cni    = {}
    kube-proxy = {}
  }

  enable_karpenter = true
  karpenter_node = {
    # Use static name so that it matches what is defined in `az1.yaml` example manifest
    iam_role_use_name_prefix = false
  }

  tags = local.tags
}

resource "aws_eks_access_entry" "karpenter_node_access_entry_cell1" {
  cluster_name      = module.eks_cell1.cluster_name
  principal_arn     = module.eks_blueprints_addons_cell1.karpenter.node_iam_role_arn
  type              = "EC2_LINUX"
  
  lifecycle {
    ignore_changes = [
      user_name
    ]
  }
}
