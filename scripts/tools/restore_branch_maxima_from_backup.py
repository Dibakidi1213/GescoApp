#!/usr/bin/env python3
"""Restore `bulletin_branches.max_exam_2` values from a backup SQLite DB.

Usage:
  python scripts/restore_branch_maxima_from_backup.py [--backup PATH] [--apply]

By default this runs in dry-run mode and writes `branch_maxima_preview.csv` with
the differences between the backup and the current DB. Pass `--apply` to update
the live DB (a safety copy is created beforehand).
"""
import argparse
import sqlite3
import csv
import shutil
import glob
import os
import time


def find_latest_backup():
    files = sorted(glob.glob('gescoapp.db.bak_*'), key=os.path.getmtime, reverse=True)
    return files[0] if files else None


def load_branch_maxima(conn):
    cur = conn.cursor()
    cur.execute('SELECT id, name, max_exam_2 FROM bulletin_branches')
    return {row[0]: (row[1], float(row[2]) if row[2] is not None else None) for row in cur.fetchall()}


def write_csv(rows, path='branch_maxima_preview.csv'):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['id', 'name', 'current_max_exam_2', 'backup_max_exam_2'])
        for r in rows:
            w.writerow(r)
    return path


def backup_current_db(path='gescoapp.db'):
    ts = time.strftime('%Y%m%d_%H%M%S')
    dest = f"{path}.pre_restore_{ts}"
    shutil.copy2(path, dest)
    return dest


def apply_updates(conn, updates):
    cur = conn.cursor()
    for bid, new_max in updates.items():
        cur.execute('UPDATE bulletin_branches SET max_exam_2 = ? WHERE id = ?', (new_max, bid))
    conn.commit()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--backup', '-b', help='Path to backup DB file (optional). If omitted the latest `gescoapp.db.bak_*` is used.')
    p.add_argument('--db', default='gescoapp.db', help='Path to current DB (default: gescoapp.db)')
    p.add_argument('--apply', action='store_true', help='Apply changes to the current DB')
    p.add_argument('--csv', default='branch_maxima_preview.csv', help='CSV output path for preview')
    args = p.parse_args()

    backup_path = args.backup or find_latest_backup()
    if not backup_path or not os.path.exists(backup_path):
        print('No backup found. Provide --backup PATH or create a backup file named gescoapp.db.bak_<ts>')
        return 2

    print(f'Using backup: {backup_path}')
    print(f'Current DB: {args.db}')

    b_conn = sqlite3.connect(backup_path)
    c_conn = sqlite3.connect(args.db)

    try:
        backup_map = load_branch_maxima(b_conn)
        current_map = load_branch_maxima(c_conn)

        diffs = []
        updates = {}
        for bid, (bname, bmax) in backup_map.items():
            if bid in current_map:
                cname, cmax = current_map[bid]
                if (bmax is None and cmax is not None) or (bmax is not None and cmax is None) or (bmax != cmax):
                    diffs.append((bid, cname or bname or '', cmax, bmax))
                    updates[bid] = bmax

        print(f'Found {len(diffs)} differing branches between backup and current DB')
        if not diffs:
            return 0

        csv_path = write_csv(diffs, args.csv)
        print('Preview CSV written to', csv_path)

        if args.apply:
            print('Creating safety copy of current DB...')
            safe_copy = backup_current_db(args.db)
            print('Safety copy:', safe_copy)
            # Apply updates (convert None to NULL)
            to_apply = {bid: (None if updates[bid] is None else updates[bid]) for bid in updates}
            apply_updates(c_conn, to_apply)
            print('Applied updates to current DB. Total updated rows:', len(to_apply))
            print('Recommendation: review', csv_path)
        else:
            print('Dry-run mode (no changes applied). Use --apply to update the DB after review.')

    finally:
        b_conn.close()
        c_conn.close()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
