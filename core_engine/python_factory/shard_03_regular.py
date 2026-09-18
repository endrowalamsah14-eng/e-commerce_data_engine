import psycopg2
from psycopg2.extras import execute_values
import random
import uuid
from datetime import datetime

DB_HOST = "127.0.0.1"
DB_PORT = "5434" 
DB_NAME = "emarkrtz_shard_03"
DB_USER = "emarkrtz_admin"
DB_PASS = "EnterpriseSkew2026!"

def get_connection():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)

def generate_regular_shard_03(target_rows=1000000, batch_size=5000):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now()
    
    # 1. SETUP MASTER DATA (Toko Biasa)
    store_id = uuid.uuid4().hex
    execute_values(cur, "INSERT INTO stores (store_id, store_name, tier, created_at) VALUES %s", [(store_id, "Toko Elektronik Standar", "Basic", now)])
    
    products = [(uuid.uuid4().hex, store_id, f"SKU-ELC-{i}", "Aksesoris Elektronik", 150000.0, False) for i in range(50)]
    inventories = [(uuid.uuid4().hex, store_id, p[0], 5000, 0, now) for p in products]
    
    execute_values(cur, "INSERT INTO products (product_id, store_id, sku, title, price, is_flash_sale) VALUES %s", products)
    execute_values(cur, "INSERT INTO inventory (inventory_id, store_id, product_id, available_qty, reserved_qty, updated_at) VALUES %s", inventories)
    
    customers = [(uuid.uuid4().hex, store_id, f"guest_elc_{i}@email.com", "guest") for i in range(1000)]
    execute_values(cur, "INSERT INTO customers (customer_id, store_id, email, segment) VALUES %s", customers)
    conn.commit()
    print("Master Data Shard 03 Siap!")

    # 2. GENERATE TRANSAKSI NORMAL
    product_ids = [p[0] for p in products]
    try:
        for i in range(0, target_rows, batch_size):
            orders_data, order_lines_data = [], []
            for _ in range(batch_size):
                customer = random.choice(customers)
                order_id = uuid.uuid4().hex
                
                num_items = random.randint(1, 3) # Pembelian wajar
                total_amount = 0
                for _ in range(num_items):
                    chosen_product = random.choice(product_ids) # Distribusi merata
                    qty = 1
                    total_amount += 150000.0
                    order_lines_data.append((uuid.uuid4().hex, order_id, store_id, chosen_product, qty, 150000.0, 150000.0))
                
                orders_data.append((order_id, store_id, customer[0], "PAID", total_amount, "E_WALLET", datetime.now(), datetime.now()))
                
            execute_values(cur, "INSERT INTO orders (order_id, store_id, customer_id, status, total_amount, payment_method, created_at, updated_at) VALUES %s", orders_data)
            execute_values(cur, "INSERT INTO order_lines (line_id, order_id, store_id, product_id, quantity, unit_price, subtotal) VALUES %s", order_lines_data)
            conn.commit()
            print(f"[Shard 03] {i + batch_size} Pesanan normal mendarat.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_regular_shard_03(target_rows=1000000, batch_size=5000)
