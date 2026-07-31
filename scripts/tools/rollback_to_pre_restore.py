#!/usr/bin/env python3
"""Restore the latest `gescoapp.db.pre_restore_*` file back to `gescoapp.db`.
Creates no extra backups; designed to be run interactively after confirmation.
"""
import glob
import os
import shutil
import sys

backs = sorted(glob.glob('gescoapp.db.pre_restore_*'), key=os.path.getmtime, reverse=True)
if not backs:
    print('NO_BACKUP')
    sys.exit(2)
src = backs[0]
shutil.copy2(src, 'gescoapp.db')
print('RESTORED', src)
sys.exit(0)
