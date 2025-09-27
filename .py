import sqlite3
from flask_bcrypt import Bcrypt

db_file = "jemtech_event_hub.db"
bcrypt = Bcrypt()

# Connect to DB
conn = sqlite3.connect(db_file)
cur = conn.cursor()

# Generate bcrypt hash for 'admin123'
password = "admin123"
hashed = bcrypt.generate_password_hash(password).decode('utf-8')

# Update admin user (id=1)
cur.execute("UPDATE user SET password_hash = ?, is_active = 1 WHERE id = 1", (hashed,))
conn.commit()
conn.close()

print("✅ Admin password reset with bcrypt. Username: 'admin', Password: 'admin123'")
