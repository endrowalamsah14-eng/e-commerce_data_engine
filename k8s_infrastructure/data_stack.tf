# ==============================================================================
# CORE NAMESPACE
# ==============================================================================
resource "kubernetes_namespace" "data_stack" {
  metadata {
    name = "emarkrtz-production"
  }
}

resource "helm_release" "local_path_provisioner" {
  name       = "local-path-provisioner"
  repository = "https://charts.containeroo.ch"
  chart      = "local-path-provisioner"
  namespace  = "kube-system"

  values = [
    yamlencode({
      storageClass = {
        defaultClass = true
      }
    })
  ]
}

resource "helm_release" "temporal_postgresql" {
  name       = "temporal-postgresql"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  version    = "15.5.38"
  namespace  = kubernetes_namespace.data_stack.metadata[0].name

  values = [yamlencode({
    image = {
      repository = "bitnamilegacy/postgresql"
      tag        = "16.4.0-debian-12-r14"
    }
    auth = {
      username = "temporal"
      password = "temporal-dev-password"
      database = "temporal"
    }
    primary = {
      persistence = {
        enabled      = true
        storageClass = "local-path"
        size         = "8Gi"
      }
      resources = {
        requests = {
          cpu    = "250m"
          memory = "512Mi"
        }
        limits = {
          cpu    = "500m"
          memory = "1Gi"
        }
      }
    }
  })]
}

resource "helm_release" "cert_manager" {
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = "v1.16.2"
  namespace        = "cert-manager"
  create_namespace = true

  values = [
    yamlencode({
      crds = {
        enabled = true
      }
    })
  ]
}

# ==============================================================================
# 1. THE CONTROL PLANE (ORCHESTRATOR)
# ==============================================================================
resource "helm_release" "temporal" {
  name             = "temporal"
  repository       = "https://go.temporal.io/helm-charts"
  chart            = "temporal"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/temporal-values.yaml")]

  depends_on = [helm_release.temporal_postgresql]
}

# ==============================================================================
# 2. THE INGESTION & MESSAGE BUS (NON-JVM)
# ==============================================================================
resource "helm_release" "redpanda" {
  name             = "redpanda"
  repository       = "https://charts.redpanda.com"
  chart            = "redpanda"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/redpanda-values.yaml")]
}

# ==============================================================================
# 2.5 DEBEZIUM KAFKA CONNECT (REPLACING PEERDB)
# ==============================================================================
resource "kubernetes_deployment" "debezium" {
  metadata {
    name      = "debezium-connect"
    namespace = kubernetes_namespace.data_stack.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "debezium-connect"
      }
    }
    template {
      metadata {
        labels = {
          app = "debezium-connect"
        }
      }
      spec {
        container {
          name  = "debezium"
          image = "quay.io/debezium/connect:2.4"
          port {
            container_port = 8083
          }
          env {
            name  = "BOOTSTRAP_SERVERS"
            value = "redpanda-0.redpanda.emarkrtz-production.svc.cluster.local:9093"
          }
          env {
            name  = "GROUP_ID"
            value = "debezium-cluster"
          }
          env {
            name  = "CONFIG_STORAGE_TOPIC"
            value = "debezium_configs"
          }
          env {
            name  = "OFFSET_STORAGE_TOPIC"
            value = "debezium_offsets"
          }
          env {
            name  = "STATUS_STORAGE_TOPIC"
            value = "debezium_statuses"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "debezium_svc" {
  metadata {
    name      = "debezium-api"
    namespace = kubernetes_namespace.data_stack.metadata[0].name
  }
  spec {
    selector = {
      app = "debezium-connect"
    }
    port {
      port        = 8083
      target_port = 8083
    }
  }
}

# ==============================================================================
# 3. THE PROCESSING, CONTRACTS, & ROUTING
# ==============================================================================
resource "helm_release" "benthos" {
  name             = "benthos-router"
  repository       = "https://benthosdev.github.io/charts"
  chart            = "benthos"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/benthos-values.yaml")]

  depends_on = [helm_release.redpanda]
}

# ==============================================================================
# 4. THE DESTINATIONS (TRIPLE-PRONGED ATTACK)
# ==============================================================================
resource "helm_release" "redis" {
  name       = "redis"
  repository = "oci://registry-1.docker.io/bitnamicharts" 
  chart      = "redis"
  version    = "19.6.1"
  namespace  = kubernetes_namespace.data_stack.metadata[0].name

  values = [file("${path.module}/values/redis-values.yaml")]

  wait = false
}

resource "helm_release" "risingwave" {
  name             = "risingwave"
  repository       = "https://risingwavelabs.github.io/helm-charts"
  chart            = "risingwave"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/risingwave-values.yaml")]
}

resource "helm_release" "minio" {
  name             = "minio"
  repository       = "https://charts.min.io/"
  chart            = "minio"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/minio-values.yaml")]
}

resource "helm_release" "starrocks" {
  name             = "starrocks"
  repository       = "https://starrocks.github.io/starrocks-kubernetes-operator"
  chart            = "kube-starrocks"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/starrocks-values.yaml")]

  depends_on = [helm_release.minio]
}

# ==============================================================================
# 5. BUSINESS INTELLIGENCE
# ==============================================================================
resource "helm_release" "metabase" {
  name             = "metabase"
  repository       = "https://pmint93.github.io/helm-charts"
  chart            = "metabase"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/metabase-values.yaml")]

  depends_on = [helm_release.starrocks]
}