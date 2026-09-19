# 🚀 BLUEPRINT: E-MARKRTZ DATA ENGINE
> **THE "JAVA KILLER" ARCHITECTURE**

| Properti              | Detail Project                                         |
| :-------------------- | :----------------------------------------------------- |
| **Status**            | 🟢 READY FOR DEPLOYMENT                                |
| **Target Deployment** | Hetzner VPS / Kubernetes                               |
| **Filosofi Sistem**   | Non-JVM, Ultra-Low Latency, Scalable, Production-Ready |

---

## 🏗️ 1. TOPOLOGI & MAPPING ROUTE (THE DATA HIGHWAY)

> [!INFO] **Konsep Inti Arsitektur**
> Arsitektur ini memisahkan **"Dunia Simulator" (PostgreSQL)** dengan **"Dunia Produksi" (Data Stack)**. Kedua dunia ini dihubungkan oleh sebuah *Data Highway* berkecepatan tinggi yang dikendalikan secara sentral, dilindungi oleh Data Contracts yang ketat di setiap *layer*.

### 📊 Peta Lengkap Aliran Data & Pipeline (Monospace Map)

```text
======================================================================================
  [ THE CONTROL PLANE (ORCHESTRATOR) ]
======================================================================================
  🧠 TEMPORAL.IO WORKFLOW ORCHESTRATOR
   ├──> Menjadwalkan Pipeline (Triggering)
   ├──> Memantau Kesehatan Aliran Data (Observability)
   ├──> Otomatisasi Retry/Self-Healing (Resilience)
   └──> Mengatur Dependency Antar-Layer (DAG Management)

======================================================================================
  [ THE SIMULATOR (DATA GENERATION) ]
======================================================================================
  🐍 PYTHON MOCK ENGINE (Zipfian Skew / Write Amplification)
       │
       ▼ (Insert & Update 9+ Juta Baris)
  🐘 POSTGRESQL SHARDING (Homogeneous)
   ├──> [ Pod 1: Shard Heavy / The Warzone ] (Port: 5432) ─┐
   ├──> [ Pod 2: Shard Regular A ] (Port: 5433)           ─┼─ (wal_level=logical)
   └──> [ Pod 3: Shard Regular B ] (Port: 5434)           ─┘

======================================================================================
  [ THE INGESTION & MESSAGE BUS (NON-JVM) ]
======================================================================================
   ┌─────────────────────────────────────────────────────────────┐
   │ ⚡ PEERDB CORE (Rust/Go Engine)                              │
   │    Tugas: Nyedot CDC (Change Data Capture) dari 3 Shard     │
   │    Tuning: Batch Size dioptimalkan untuk Shard Heavy        │
   └────────────────┬────────────────────────────────────────────┘
                    │ (Payload CDC / JSONB)
                    ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ 🚄 REDPANDA (C++ Kafka Alternative)                         │
   │    Topik: cdc.all_shards.orders & cdc.all_shards.order_lines│
   └────────────────┬────────────────────────────────────────────┘
                    │
======================================================================================
  [ THE PROCESSING, CONTRACTS, & ROUTING (THE BENTHOS FORK) ]
======================================================================================
   ┌─────────────────────────────────────────────────────────────┐
   │ 🔀 BENTHOS (Go) SINK, FLATTENING, & DATA CONTRACT           │
   │    Tugas: Validasi Skema (Contract), Pembersihan Bloblang,  │
   │           Flattening JSON, & Dynamic Routing.               │
   └─┬─────────────────────────────────────────────────────────┬─┘
     │ (Data Valid / Lolos Skema)                              │ (Data Cacat / Error)
     ▼                                                         ▼
(Ke 3 Jalur Utama)                                  ┌────────────────────┐
                                                    │ 🚷 DLQ TOPIC       │
                                                    │ (Karantina Data)   │
                                                    │ + Error Metadata   │
                                                    │ + Re-inject Script │
                                                    └────────────────────┘
======================================================================================
  [ THE DESTINATIONS (TRIPLE-PRONGED ATTACK) ]
======================================================================================

  ⬇️ JALUR 1          ⬇️ JALUR 2          ⬇️ JALUR 3
 (Hot Operational)   (Real-Time Alerts)  (Historical Lakehouse)

 ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐
 │ Benthos Sink │    │ RisingWave   │    │ Benthos Sink       │
 └──────┬───────┘    └──────┬───────┘    └─────────┬──────────┘
        │                   │                      │ (Flat Parquet/Iceberg)
        ▼                   ▼                      ▼
 ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐
 │ ScyllaDB     │    │ Real-Time DB │    │ MinIO (Bronze)     │
 │ (C++ NoSQL)  │    │ (Mat. Views) │    │ (S3 Compatible)    │
 │- Active Cart │    │- Bot Alerts  │    └─────────┬──────────┘
 │  (w/ TTL)    │    │- Hot Stocks  │              │ (Zero-Copy Read via Iceberg)
 │- User Sess.  │    │- Top Products│              ▼
 │  (Auto Purge)│    └──────────────┘    ┌────────────────────┐
 └──────────────┘                        │ StarRocks (OLAP)   │
                                         │ (C++ Query Engine) │
                                         └─────────┬──────────┘
                                                   │ (SQL Transform & Data
                                                   │  Contract Validation
                                                   │  via dbt core + tests)
                                                   ▼
                                         ┌────────────────────┐
                                         │ MinIO (Silver/Gold)│
                                         │ - Clean Iceberg    │
                                         │ - DLQ/Audit Tables │
                                         └─────────┬──────────┘
                                                   │
                                                   ▼
                                         ┌────────────────────┐
                                         │ Metabase (BI)      │
                                         │ (Business Dash.)   │
                                         └────────────────────┘