import pandas as pd
import sqlite3
import os

# ==== CSV FILE PATHS ====
# Change these to the actual local Google Drive paths on your machine
providers_csv = r"H:\My Drive\providers_data.csv"
receivers_csv = r"H:\My Drive\receivers_data.csv"
food_listings_csv = r"H:\My Drive\food_listings_data.csv"
claims_csv = r"H:\My Drive\claims_data.csv"

# ==== DATABASE FILE ====
db_path = "food_donation.db"

# Remove old DB if exists (start fresh)
if os.path.exists(db_path):
    os.remove(db_path)

# Connect to SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ==== CREATE TABLES ====
cursor.execute("""
CREATE TABLE providers (
    Provider_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Type TEXT,
    Address TEXT,
    City TEXT,
    Contact TEXT
);
""")

cursor.execute("""
CREATE TABLE receivers (
    Receiver_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Type TEXT,
    City TEXT,
    Contact TEXT
);
""")

cursor.execute("""
CREATE TABLE food_listings (
    Food_ID INTEGER PRIMARY KEY,
    Food_Name TEXT,
    Quantity INTEGER,
    Expiry_Date DATE,
    Provider_ID INTEGER,
    Provider_Type TEXT,
    Location TEXT,
    Food_Type TEXT,
    Meal_Type TEXT,
    FOREIGN KEY (Provider_ID) REFERENCES providers(Provider_ID)
);
""")

cursor.execute("""
CREATE TABLE claims (
    Claim_ID INTEGER PRIMARY KEY,
    Food_ID INTEGER,
    Receiver_ID INTEGER,
    Status TEXT,
    Timestamp DATETIME,
    FOREIGN KEY (Food_ID) REFERENCES food_listings(Food_ID),
    FOREIGN KEY (Receiver_ID) REFERENCES receivers(Receiver_ID)
);
""")

# ==== LOAD CSV DATA INTO TABLES ====
pd.read_csv(providers_csv).to_sql("providers", conn, if_exists="append", index=False)
pd.read_csv(receivers_csv).to_sql("receivers", conn, if_exists="append", index=False)
pd.read_csv(food_listings_csv).to_sql("food_listings", conn, if_exists="append", index=False)
pd.read_csv(claims_csv).to_sql("claims", conn, if_exists="append", index=False)

# Commit & Close
conn.commit()
conn.close()

print("✅ Database created with correct schema, primary keys, and foreign keys. Data loaded successfully!")
