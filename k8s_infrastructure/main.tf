resource "hcloud_ssh_key" "k8s_admin" {
  name       = "k8s_admin_key"
  public_key = file("~/.ssh/id_rsa_k8s.pub")
}

resource "hcloud_server" "k8s_production" {
  name        = "emarkrtz-k8s-prod"
  image       = "ubuntu-24.04"
  server_type = "cpx42" # 🔥 8 vCPU, 16GB RAM
  location    = "nbg1"
  ssh_keys    = [hcloud_ssh_key.k8s_admin.id]

  # Cloud-Init: Instalasi Kubeadm, Kubelet, Kubectl, dan Containerd
  user_data = <<-EOF
    #!/bin/bash
    set -e

    # 1. Persiapan Kernel & Networking untuk K8s
    cat <<EOT | tee /etc/modules-load.d/k8s.conf
    overlay
    br_netfilter
    EOT
    modprobe overlay
    modprobe br_netfilter

    cat <<EOT | tee /etc/sysctl.d/k8s.conf
    net.bridge.bridge-nf-call-iptables  = 1
    net.bridge.bridge-nf-call-ip6tables = 1
    net.ipv4.ip_forward                 = 1
    EOT
    sysctl --system

    # 2. Instalasi Container Runtime (Containerd)
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg lsb-release apt-transport-https
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y containerd.io
    containerd config default > /etc/containerd/config.toml
    sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
    systemctl restart containerd
    systemctl enable containerd

    # 3. Instalasi Komponen Kubernetes (v1.30)
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list
    apt-get update -y
    apt-get install -y kubelet kubeadm kubectl
    apt-mark hold kubelet kubeadm kubectl

    # 4. Inisialisasi K8s Control Plane
    kubeadm init --pod-network-cidr=10.244.0.0/16 --ignore-preflight-errors=NumCPU

    # 5. Konfigurasi Akses Kubeconfig
    mkdir -p /root/.kube
    cp -i /etc/kubernetes/admin.conf /root/.kube/config
    chown $(id -u):$(id -g) /root/.kube/config

    # 6. Pasang Jaringan Pod (Flannel CNI)
    export KUBECONFIG=/etc/kubernetes/admin.conf
    kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

    # 7. Hapus Taint agar Pods Produksi bisa jalan di Node ini
    kubectl taint nodes --all node-role.kubernetes.io/control-plane-
  EOF
}

output "k8s_public_ip" {
  description = "IP Publik K8s Produksi & Simulator"
  value       = hcloud_server.k8s_production.ipv4_address
}
