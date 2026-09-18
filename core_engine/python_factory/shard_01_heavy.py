import psycopg2
from psycopg2.extras import execute_values
import random
import uuid
from datetime import datetime

DB_HOST = "127.0.0.1"
DB_PORT = "5432" 
DB_NAME = "emarkrtz_shard_01"
DB_USER = "emarkrtz_admin"
DB_PASS = "EnterpriseSkew2026!"

def get_connection():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)

def generate_heavy_shard(target_rows=1000000, batch_size=5000):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now()
    
    # 1. SETUP MASTER DATA (Cuma ada 1 Toko: The Heavy Tenant)
    heavy_store_id = uuid.uuid4().hex
    execute_values(cur, "INSERT INTO stores (store_id, store_name, tier, created_at) VALUES %s ON CONFLICT DO NOTHING", 
                   [(heavy_store_id, "E-Markrtz Official Heavy", "Enterprise", now)])
    
    flash_shoe = uuid.uuid4().hex
    products = [(flash_shoe, heavy_store_id, "SKU-HEAVY-99", "Sepatu Jordan Diskon 99%", 15000.00, True)]
    inventories = [(uuid.uuid4().hex, heavy_store_id, flash_shoe, 500, 0, now)]
    
    for _ in range(20): # Barang pelengkap
        p_id = uuid.uuid4().hex
        products.append((p_id, heavy_store_id, f"SKU-{random.randint(1000, 9999)}", "Barang Reguler", 50000.0, False))
        inventories.append((uuid.uuid4().hex, heavy_store_id, p_id, 1000, 0, now))
        
    execute_values(cur, "INSERT INTO products (product_id, store_id, sku, title, price, is_flash_sale) VALUES %s", products)
    execute_values(cur, "INSERT INTO inventory (inventory_id, store_id, product_id, available_qty, reserved_qty, updated_at) VALUES %s", inventories)
    
    customers = [(uuid.uuid4().hex, heavy_store_id, f"user_{i}@email.com", random.choices(['loyal_user', 'bot_reseller'], [80, 20])[0]) for i in range(1000)]
    execute_values(cur, "INSERT INTO customers (customer_id, store_id, email, segment) VALUES %s", customers)
    
    conn.commit()
    print("Master Data Shard 01 (Heavy) Siap! Memulai gempuran...")

    # 2. THE CHAOS ENGINE (1 Juta Transaksi Berdarah)
    product_ids = [p[0] for p in products]
    try:
        for i in range(0, target_rows, batch_size):
            orders_data, order_lines_data = [], []
            for _ in range(batch_size):
                customer = random.choice(customers)
                order_id = uuid.uuid4().hex
                
                # SKEW LOGIC: Jika Bot, keranjang isi 30-50. Jika bukan, isi 1-2.
                is_bot = customer[3] == 'bot_reseller'
                num_items = random.randint(30, 50) if is_bot else random.randint(1, 2)
                
                total_amount = 0
                for _ in range(num_items):
                    # SKEW LOGIC: 95% nembak barang Flash Sale
                    chosen_product = random.choices([flash_shoe, random.choice(product_ids)], [95, 5])[0]
                    qty = random.randint(5, 10) if is_bot else 1
                    total_amount += (qty * 15000.0)
                    order_lines_data.append((uuid.uuid4().hex, order_id, heavy_store_id, chosen_product, qty, 15000.0, qty * 15000.0))
                
                orders_data.append((order_id, heavy_store_id, customer[0], "PENDING", total_amount, "CREDIT_CARD", datetime.now(), datetime.now()))
                
            execute_values(cur, "INSERT INTO orders (order_id, store_id, customer_id, status, total_amount, payment_method, created_at, updated_at) VALUES %s", orders_data)
            execute_values(cur, "INSERT INTO order_lines (line_id, order_id, store_id, product_id, quantity, unit_price, subtotal) VALUES %s", order_lines_data)
            conn.commit()
            print(f"[Shard 01] {i + batch_size} Pesanan mendarat. Bot aktif.")
    except Exception as e:
        print(f"[Shard 01] MACET (Lock Contention): {e}")
        conn.rollback()

if __name__ == "__main__":
    generate_heavy_shard(target_rows=1000000, batch_size=5000)
