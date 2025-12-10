import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=== Migrations appliquées pour 'assets' ===")
rows = cursor.execute(
    "SELECT id, app, name, applied FROM django_migrations WHERE app='assets' ORDER BY id"
).fetchall()

for row in rows:
    print(f"ID: {row[0]} | App: {row[1]} | Name: {row[2]} | Applied: {row[3]}")

print("\n=== Colonnes de la table assets_attribution ===")
columns = cursor.execute("PRAGMA table_info(assets_attribution)").fetchall()
for col in columns:
    print(f"ID: {col[0]} | Name: {col[1]} | Type: {col[2]} | NotNull: {col[3]} | Default: {col[4]}")

conn.close()
