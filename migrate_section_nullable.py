#!/usr/bin/env python
# Migration script for making section_id nullable

from app import app, db
import mysql.connector
from config import Config

# Parse the database URI
uri_parts = Config.SQLALCHEMY_DATABASE_URI.split('://')[-1]
user_pass, host_db = uri_parts.split('@')
user, password = user_pass.split(':')
host, database = host_db.split('/')

# Connect and execute migration
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password if password else None,
    database=database
)

cursor = conn.cursor()

# Execute the migration
sql = "ALTER TABLE courses MODIFY section_id INT NULL"
cursor.execute(sql)
conn.commit()

print("✅ Migration exécutée: section_id is now nullable in courses table")

cursor.close()
conn.close()
