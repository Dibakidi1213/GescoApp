import glob, os
files = glob.glob('gescoapp.db.bak_*')
files.sort(key=os.path.getmtime, reverse=True)
for f in files:
    print(f)