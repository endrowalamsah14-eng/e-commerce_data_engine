import requests
import json
import time

# PeerDB API Endpoints
PEERS_API_URL = "http://localhost:3001/api/v1/peers/create"
# FIX MUTLAK: Endpoint validasi yang benar sesuai tangkapan UI
FLOWS_VALIDATE_URL = "http://localhost:3001/api/v1/flows/cdc/validate" 
FLOWS_API_URL = "http://localhost:3001/api/v1/flows/cdc/create"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

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

tables_to_sync = ["stores", "products", "inventory", "customers", "orders", "order_lines"]

print("🛠️ [Phase 1] Registering infrastructure peers to PeerDB...")

kafka_payload = {
    "peer": {
        "name": TARGET_PEER_NAME,
        "type": 9,
        "kafkaConfig": {
            "servers": ["redpanda-0.redpanda.emarkrtz-production.svc.cluster.local:9093"],
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
except Exception as e:
    print(f"❌ Error registering Redpanda target: {e}")

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
    except Exception as e:
        print(f"❌ Error registering {shard['name']}: {e}")


print("\n🔥 [Phase 1.5] Warming up PeerDB Catalog Cache (Mimicking UI Background Tasks)...")
# Trik Hacker: Kita bombardir endpoint katalog mereka persis kayak UI biar tabelnya kebaca
for shard in shards_config:
    s_name = shard["name"]
    print(f"   -> Forcing catalog sync for {s_name}...")
    
    warmup_urls = [
        f"http://localhost:3001/api/v1/schemas?peer_name={s_name}",
        f"http://localhost:3001/api/v1/tables?peerName={s_name}"
    ]
    for url in warmup_urls:
        try: requests.get(url, timeout=2)
        except: pass
        
    for table in tables_to_sync:
        table_urls = [
            f"http://localhost:3001/api/v1/columns?peer_name={s_name}&tableName=public.{table}",
            f"http://localhost:3001/api/v1/columns?peerName={s_name}&tableName=public.{table}"
        ]
        for url in table_urls:
            try: requests.get(url, timeout=2)
            except: pass

print("⏳ Waiting 10 seconds for backend to fully cache the tables...")
time.sleep(10)


print("\n🚀 [Phase 2] Assembling CDC Pipelines (Flows)...")
for shard in shards_config:
    s_name = shard["name"]
    d_name = TARGET_PEER_NAME
    f_job_name = f"cdc_{s_name}_to_redpanda"
    
    table_mappings = [
        {
            "sourceTableIdentifier": f"public.{table}",
            "destinationTableIdentifier": f"public.{table}",
            "bigqueryCdcEventsFunction": 1,
            "columns": [],
            "engine": 0,
            "exclude": [],
            "partitionByExpr": "",
            "partitionKey": "",
            "policyName": "",
            "queryCdcWatermarkColumn": "",
            "shardingKey": ""
        } for table in tables_to_sync
    ]
    
    flow_payload = {
        "connectionConfigs": {
            "sourceName": s_name,
            "destinationName": d_name,
            "flowJobName": f_job_name
        },
        "cdcStagingPath": "",
        "destinationName": d_name,
        "disablePeerDBColumns": False,
        "doInitialSnapshot": True,
        "env": {},
        "envString": "",
        "flags": [],
        "flowJobName": f_job_name,
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
        "sourceName": s_name,
        "syncedAtColName": "_PEERDB_SYNCED_AT",
        "system": 0,
        "tableMappings": table_mappings,
        "version": 0
    }
    
    try:
        # STEP 1: Pancing validasi dengan URL yang sudah benar
        print(f"🔍 Validating mirror: {f_job_name}...")
        val_res = requests.post(FLOWS_VALIDATE_URL, headers=HEADERS, data=json.dumps(flow_payload))
        
        if val_res.status_code == 200:
            print(f"✅ Validation successful for {f_job_name}. Proceeding to create...")
            
            # STEP 2: Eksekusi creation
            print(f"⏳ Provisioning mirror: {f_job_name}...")
            res = requests.post(FLOWS_API_URL, headers=HEADERS, data=json.dumps(flow_payload))
            
            if res.status_code == 200:
                print(f"✅ Success! Pipeline {f_job_name} is now airborne.")
            else:
                print(f"❌ Failed to provision {f_job_name}. Status: {res.status_code} | Response: {res.text}")
        else:
            print(f"❌ Validation failed for {f_job_name}. Status: {val_res.status_code} | Response: {val_res.text}")
            
    except Exception as e:
        print(f"⚠️ Connection error occurred while processing {s_name}: {e}")

print("\n🎉 Automated infrastructure provisioning completed successfully!")