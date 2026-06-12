"""
Run this once to create sample analytics data for testing.
python seed.py
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/analytics")
engine = create_engine(DATABASE_URL)

SEED_SQL = """
-- Sales table
CREATE TABLE IF NOT EXISTS sales (
    id          SERIAL PRIMARY KEY,
    date        DATE NOT NULL,
    region      VARCHAR(50),
    product     VARCHAR(100),
    category    VARCHAR(50),
    revenue     NUMERIC(10,2),
    units_sold  INTEGER,
    customer_id INTEGER
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100),
    email       VARCHAR(150),
    country     VARCHAR(50),
    segment     VARCHAR(50),
    joined_date DATE
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100),
    category    VARCHAR(50),
    price       NUMERIC(10,2),
    stock       INTEGER
);

-- Insert sample customers
INSERT INTO customers (name, email, country, segment, joined_date)
SELECT
    'Customer ' || i,
    'customer' || i || '@email.com',
    (ARRAY['India','USA','UK','Germany','Australia'])[1 + (i % 5)],
    (ARRAY['Enterprise','SMB','Startup','Individual'])[1 + (i % 4)],
    NOW() - (random() * 365 * 2 || ' days')::interval
FROM generate_series(1, 200) i
ON CONFLICT DO NOTHING;

-- Insert sample products
INSERT INTO products (name, category, price, stock)
VALUES
    ('Cardivax 10mg', 'Cardiology',   299.99, 500),
    ('Neurofix 5mg',  'Neurology',    199.99, 300),
    ('Immunoboost',   'Immunology',   149.99, 800),
    ('Diabecare',     'Endocrinology',249.99, 400),
    ('Respiclear',    'Pulmonology',  179.99, 600),
    ('Arthroease',    'Rheumatology', 219.99, 350),
    ('Hepatoguard',   'Hepatology',   329.99, 250),
    ('Oncoshield',    'Oncology',     599.99, 150)
ON CONFLICT DO NOTHING;

-- Insert sample sales (last 12 months)
INSERT INTO sales (date, region, product, category, revenue, units_sold, customer_id)
SELECT
    NOW()::date - (random() * 365)::integer,
    (ARRAY['North','South','East','West','Central'])[1 + (i % 5)],
    (ARRAY['Cardivax 10mg','Neurofix 5mg','Immunoboost','Diabecare','Respiclear','Arthroease','Hepatoguard','Oncoshield'])[1 + (i % 8)],
    (ARRAY['Cardiology','Neurology','Immunology','Endocrinology','Pulmonology','Rheumatology','Hepatology','Oncology'])[1 + (i % 8)],
    (random() * 5000 + 500)::numeric(10,2),
    (random() * 50 + 1)::integer,
    (random() * 200 + 1)::integer
FROM generate_series(1, 1000) i;
"""

with engine.connect() as conn:
    conn.execute(text(SEED_SQL))
    conn.commit()
    print("✓ Sample data created: sales, customers, products tables")
    print("✓ 1000 sales records, 200 customers, 8 products")
