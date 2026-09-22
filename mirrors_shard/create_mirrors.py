import requests
import json

# API Endpoint menggunakan rute flows yang baru ditemukan
API_URL = "http://localhost:3001/api/v1/flows/cdc/create"

shards = ["emarkrtz_shard_01", "emarkrtz_shard_02", "emarkrtz_shard_03"]
target_peer = "redpanda_target"
tables_to_sync = ["stores", "products", "inventory", "customers", "orders", "order_lines"]

headers = {"Content-Type": "application/json"}

print("🚀 Initiating the automated assembly of The Java Killer CDC pipeline...")

for shard in shards:
    mirror_name = f"cdc_{shard}_to_redpanda"
    
    # Mapping tabel disesuaikan dengan format camelCase API v0.37.7
    table_mappings = [
        {
            "sourceTableIdentifier": f"public.{table}",
            "destinationTableIdentifier": f"cdc.all_shards.{table}"
        } for table in tables_to_sync
    ]
    
    # Payload direplikasi 100% presisi sesuai dengan sadapan tab Network
    payload = {
        "connectionConfigs": {
            "sourceName": shard,
            "destinationName": target_peer,
            "flowJobName": mirror_name
        },
        "cdcStagingPath": "",
        "destinationName": target_peer,
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
        "sourceName": shard,
        "syncedAtColName": "_PEERDB_SYNCED_AT",
        "system": 0,
        "tableMappings": table_mappings,
        "version": 0
    }
    
    try:
        print(f"⏳ Provisioning mirror: {mirror_name}...")
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        
        if response.status_code in [200, 201]:
            print(f"✅ Success! Pipeline {mirror_name} is now airborne.")
        else:
            print(f"❌ Failed to provision {mirror_name}. Status: {response.status_code}")
            print(f"📝 Response: {response.text}")
    except Exception as e:
        print(f"⚠️ API connection encountered an error on {shard}: {e}")

print("🎉 Execution completed!")