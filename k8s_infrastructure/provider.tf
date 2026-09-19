terraform {
  required_providers {
    # Existing Hetzner Provider
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
    # New Kubernetes Provider
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23.0"
    }
    # New Helm Provider
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11.0"
    }
  }
}

# ---------------------------------------------------------
# HETZNER CLOUD CONFIGURATION (INFRASTRUCTURE)
# ---------------------------------------------------------
variable "hcloud_token" {
  type      = string
  sensitive = true
}

provider "hcloud" {
  token = var.hcloud_token
}

# ---------------------------------------------------------
# KUBERNETES & HELM CONFIGURATION (DATA STACK DEPLOYMENT)
# ---------------------------------------------------------

# Configure the Kubernetes provider to connect to the Hetzner K8s cluster
provider "kubernetes" {
  config_path = "~/.kube/config"
}

# Configure the Helm provider with the same K8s cluster credentials
provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}