import sqlite3
import os

print("Migrating from corvus_v3.db to corvus_red.db")
v3 = sqlite3.connect('corvus_v3.db')
red = sqlite3.connect('corvus_red.db')

cursor_v3 = v3.cursor()
cursor_v3.execute("SELECT name, rows, features, file_path, created_at FROM preprocessed_datasets")
datasets = cursor_v3.fetchall()

cursor_red = red.cursor()
# Cari admin
cursor_red.execute("SELECT id FROM users LIMIT 1")
admin_id = cursor_red.fetchone()[0]

# Insert
cursor_red.executemany(
    "INSERT INTO preprocessed_datasets (user_id, name, rows, features, file_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
    [(admin_id, d[0], d[1], d[2], d[3], d[4]) for d in datasets]
)
red.commit()
print(f"Migrated {len(datasets)} datasets to admin {admin_id}")
