import sqlite3
import os

print("Migrating from corvus_v3.db to corvus_red.db")
if not os.path.isfile('corvus_v3.db'):
    print("corvus_v3.db not found. Skipping migration.")
    exit(0)

try:
    v3 = sqlite3.connect('corvus_v3.db')
    cursor_v3 = v3.cursor()
    cursor_v3.execute("SELECT name, rows, features, file_path, created_at FROM preprocessed_datasets")
    datasets = cursor_v3.fetchall()

    red = sqlite3.connect('corvus_red.db')
    cursor_red = red.cursor()
    # Cari admin
    cursor_red.execute("SELECT id FROM users LIMIT 1")
    admin = cursor_red.fetchone()
    if admin:
        admin_id = admin[0]
        # Insert
        cursor_red.executemany(
            "INSERT INTO preprocessed_datasets (user_id, name, rows, features, file_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [(admin_id, d[0], d[1], d[2], d[3], d[4]) for d in datasets]
        )
        red.commit()
        print(f"Migrated {len(datasets)} datasets to admin {admin_id}")
except sqlite3.OperationalError as e:
    print(f"Skipping migration due to error: {e}")
