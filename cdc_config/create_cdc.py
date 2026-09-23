import requests
import json
import time

# PeerDB API Endpoints
PEERS_API_URL = "http://localhost:3001/api/v1/peers/create"
FLOWS_API_URL = "http://localhost:3001/api/v1/flows/cdc/create"
HEADERS = {"Content-Type": "application/json"}

# Database Credentials & Infrastructure Targets
PG_HOST = "116.203.123.158"
PG_USER = "emarkrtz_admin"
PG_PASS = "EnterpriseSkew2026!"
TARGET_PEER_NAME = "redpanda_target"

shards_config = [
    {"name": "emarkrtz_shard_01", "port": 5432},
    {"name": "emarkrtz_shard_02", "port": 5433},
    {"name": "emarkrtz_shard_03", "port": 5434}
]

print("🛠️ [Phase 1] Registering infrastructure peers to PeerDB...")

# 1. Register the target destination (Redpanda/Kafka)
kafka_payload = {
    "peer": {
        "name": TARGET_PEER_NAME,
        "type": 9,
        "kafkaConfig": {
            "servers": [
                "redpanda-0.redpanda.emarkrtz-production.svc.cluster.local:9093"
            ],
            "disableTls": True,
            "requireTls": False,
            "skipCertVerification": False,
            "authType": 0
        }
    },
    "allowUpdate": True,
    "disableValidation": False
}

try:
    res = requests.post(PEERS_API_URL, headers=HEADERS, data=json.dumps(kafka_payload))
    if res.status_code == 200:
        print(f"✅ Target Peer successfully registered: {TARGET_PEER_NAME}")
    else:
        print(f"⚠️ Target Peer registration status: {res.text}")
except Exception as e:
    print(f"❌ Error registering Redpanda target: {e}")

# 2. Register source databases (PostgreSQL)
for shard in shards_config:
    pg_payload = {
        "peer": {
            "name": shard["name"],
            "type": 3,
            "postgresConfig": {
                "host": PG_HOST,
                "port": shard["port"],
                "user": PG_USER,
                "password": PG_PASS,
                "database": shard["name"]
            }
        },
        "allowUpdate": True,
        "disableValidation": False
    }
    
    try:
        res = requests.post(PEERS_API_URL, headers=HEADERS, data=json.dumps(pg_payload))
        if res.status_code == 200:
            print(f"✅ Source Peer successfully registered: {shard['name']}")
        else:
            print(f"⚠️ Failed to register {shard['name']}. Response: {res.text}")
    except Exception as e:
        print(f"❌ Error registering {shard['name']}: {e}")

print("\n🚀 [Phase 2] Assembling CDC Pipelines (Flows)...")
time.sleep(2) 

# 3. Provision the CDC Mirrors with 100% Hardcoded UI Payload
for shard in shards_config:
    shard_name = shard["name"]
    mirror_name = f"cdc_{shard_name}_to_redpanda"
    
    # MONOLITHIC PAYLOAD: No loops, no shortcuts. Exactly matching the UI dump.
    flow_payload = {
        "connectionConfigs": {
            "sourceName": shard_name,
            "destinationName": TARGET_PEER_NAME,
            "flowJobName": mirror_name
        },
        "cdcStagingPath": "",
        "destinationName": TARGET_PEER_NAME,
        "disablePeerDBColumns": False,
        "doInitialSnapshot": True,
        "env": {},
        "envString": "",
        "flags": [],
        "flowJobName": mirror_name,
        "idleTimeoutSeconds": 60,
        "initialSnapshotOnly": False,
        "maxBatchSize": 250000,
        "publicationName": "",
        "queryCdcPullSyncParallelism": 0,
        "replicationSlotName": "",
        "resync": False,
        "script": "",
        "skipValidation": False,
        "snapshotMaxParallelWorkers": 4,
        "snapshotNumPartitionsOverride": 0,
        "snapshotNumRowsPerPartition": 250000,
        "snapshotNumTablesInParallel": 1,
        "snapshotStagingPath": "",
        "softDeleteColName": "_PEERDB_IS_DELETED",
        "sourceName": shard_name,
        "syncedAtColName": "_PEERDB_SYNCED_AT",
        "system": 0,
        "tableMappings": [
            {
                "sourceTableIdentifier": "public.customers",
                "destinationTableIdentifier": "public.customers",
                "bigqueryCdcEventsFunction": 1,
                "columns": [],
                "engine": 0,
                "exclude": [],
                "partitionByExpr": "",
                "partitionKey": "",
                "policyName": "",
                "queryCdcWatermarkColumn": "",
                "shardingKey": ""
            },
            {
                "sourceTableIdentifier": "public.inventory",
                "destinationTableIdentifier": "public.inventory",
                "bigqueryCdcEventsFunction": 1,
                "columns": [],
                "engine": 0,
                "exclude": [],
                "partitionByExpr": "",
                "partitionKey": "",
                "policyName": "",
                "queryCdcWatermarkColumn": "",
                "shardingKey": ""
            },
            {
                "sourceTableIdentifier": "public.order_lines",
                "destinationTableIdentifier": "public.order_lines",
                "bigqueryCdcEventsFunction": 1,
                "columns": [],
                "engine": 0,
                "exclude": [],
                "partitionByExpr": "",
                "partitionKey": "",
                "policyName": "",
                "queryCdcWatermarkColumn": "",
                "shardingKey": ""
            },
            {
                "sourceTableIdentifier": "public.orders",
                "destinationTableIdentifier": "public.orders",
                "bigqueryCdcEventsFunction": 1,
                "columns": [],
                "engine": 0,
                "exclude": [],
                "partitionByExpr": "",
                "partitionKey": "",
                "policyName": "",
                "queryCdcWatermarkColumn": "",
                "shardingKey": ""
            },
            {
                "sourceTableIdentifier": "public.products",
                "destinationTableIdentifier": "public.products",
                "bigqueryCdcEventsFunction": 1,
                "columns": [],
                "engine": 0,
                "exclude": [],
                "partitionByExpr": "",
                "partitionKey": "",
                "policyName": "",
                "queryCdcWatermarkColumn": "",
                "shardingKey": ""
            },
            {
                "sourceTableIdentifier": "public.stores",
                "destinationTableIdentifier": "public.stores",
                "bigqueryCdcEventsFunction": 1,
                "columns": [],
                "engine": 0,
                "exclude": [],
                "partitionByExpr": "",
                "partitionKey": "",
                "policyName": "",
                "queryCdcWatermarkColumn": "",
                "shardingKey": ""
            }
        ],
        "version": 0
    }
    
    try:
        print(f"⏳ Provisioning mirror: {mirror_name}...")
        res = requests.post(FLOWS_API_URL, headers=HEADERS, data=json.dumps(flow_payload))
        
        if res.status_code == 200:
            print(f"✅ Success! Pipeline {mirror_name} is now airborne.")
        else:
            print(f"❌ Failed to provision {mirror_name}. Status: {res.status_code} | Response: {res.text}")
    except Exception as e:
        print(f"⚠️ Connection error occurred while processing {shard_name}: {e}")

print("\n🎉 Automated infrastructure provisioning completed successfully!")