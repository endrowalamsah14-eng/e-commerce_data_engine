# ==============================================================================
# CORE NAMESPACE
# ==============================================================================
resource "kubernetes_namespace" "data_stack" {
  metadata {
    name = "emarkrtz-production"
  }
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

resource "helm_release" "peerdb" {
  name             = "peerdb"
  repository       = "https://peerdb-io.github.io/charts"
  chart            = "peerdb"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/peerdb-values.yaml")]

  # PeerDB must wait for Redpanda to be fully operational
  depends_on = [helm_release.redpanda]
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

  # Benthos routing requires the message bus to be ready
  depends_on = [helm_release.redpanda]
}

# ==============================================================================
# 4. THE DESTINATIONS (TRIPLE-PRONGED ATTACK)
# ==============================================================================

# Route 1: Hot Operational Store
resource "helm_release" "scylladb" {
  name             = "scylladb"
  repository       = "https://scylladb.github.io/scylla-helm-charts"
  chart            = "scylla"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/scylladb-values.yaml")]
}

# Route 2: Real-Time DB & Alerts
resource "helm_release" "risingwave" {
  name             = "risingwave"
  repository       = "https://risingwavelabs.github.io/helm-charts"
  chart            = "risingwave"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/risingwave-values.yaml")]
}

# Route 3: Historical Lakehouse (Storage)
resource "helm_release" "minio" {
  name             = "minio"
  repository       = "https://charts.min.io/"
  chart            = "minio"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/minio-values.yaml")]
}

# Route 3: Historical Lakehouse (Compute & OLAP)
resource "helm_release" "starrocks" {
  name             = "starrocks"
  repository       = "https://starrocks.github.io/starrocks-kubernetes-operator"
  chart            = "kube-starrocks"
  namespace        = kubernetes_namespace.data_stack.metadata[0].name
  
  values = [file("${path.module}/values/starrocks-values.yaml")]

  # Compute engine requires Lakehouse storage to be provisioned first
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