-- ==============================================================================
-- E-MARKRTZ HOMOGENEOUS SHARD SCHEMA (The 6 Master Tables)
-- ==============================================================================

-- 1. Tabel Master Toko (The Tenant)
CREATE TABLE stores (
    store_id VARCHAR(50) PRIMARY KEY,
    store_name VARCHAR(255) NOT NULL,
    tier VARCHAR(50),
    created_at TIMESTAMP NOT NULL
);

-- 2. Tabel Katalog & Produk
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    sku VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    price DECIMAL(15, 2) NOT NULL,
    is_flash_sale BOOLEAN DEFAULT FALSE
);

-- 3. Tabel Inventory (The Warzone 🩸)
CREATE TABLE inventory (
    inventory_id VARCHAR(50) PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    available_qty INT NOT NULL DEFAULT 0,
    reserved_qty INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL
);

-- 4. Tabel Pelanggan (The Buyers)
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    segment VARCHAR(50)
);

-- 5. Tabel Transaksi / Orders (The Payload)
CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(15, 2) NOT NULL,
    payment_method VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- 6. Tabel Order Lines (The Amplifier)
CREATE TABLE order_lines (
    line_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    store_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(15, 2) NOT NULL,
    subtotal DECIMAL(15, 2) NOT NULL
);

-- ==============================================================================
-- INDEXES FOR LOCK CONTENTION & CDC PERFORMANCE
-- ==============================================================================
-- Index ini krusial biar pas Python nembak UPDATE, Postgres tau persis baris mana yang di-lock
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_order_lines_order ON order_lines(order_id);
