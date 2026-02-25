#!/usr/bin/env python3
"""List users from the instance SQLite DB.

Usage:
  python list_users.py [--csv OUTFILE] [--include-passwords]

By default prints JSON array of users (password field omitted).
"""
import argparse
import json
import os
import sqlite3
import sys

p = argparse.ArgumentParser()
p.add_argument('--csv', '-c', help='Write CSV to this path')
p.add_argument('--include-passwords', action='store_true', help='Include hashed password in output')
args = p.parse_args()

base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(base, 'instance', 'book_store.db')
if not os.path.exists(db_path):
    print(json.dumps({'error': 'db not found', 'path': db_path}))
    sys.exit(2)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
Tables = [r[0] for r in cur.fetchall()]

if 'users' not in Tables and 'user' not in Tables:
    print(json.dumps({'error': 'no users table', 'tables': Tables}))
    sys.exit(0)

table = 'users' if 'users' in Tables else 'user'
cur.execute(f"PRAGMA table_info({table})")
cols = [r[1] for r in cur.fetchall()]
cur.execute(f"SELECT * FROM {table}")
rows = cur.fetchall()

users = []
for row in rows:
    d = dict(zip(cols, row))
    if not args.include_passwords and 'password' in d:
        d.pop('password')
    users.append(d)

if args.csv:
    import csv
    with open(args.csv, 'w', newline='', encoding='utf-8') as fh:
        if users:
            writer = csv.DictWriter(fh, fieldnames=users[0].keys())
            writer.writeheader()
            for u in users:
                writer.writerow(u)
    print(json.dumps({'csv_written': args.csv, 'count': len(users)}))
else:
    print(json.dumps(users, default=str, indent=2))
