import sys

filename = 'c:/xampp2/htdocs/GescoApp - Copie/routes/professor.py'

with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# delete lines from index 433 to 627 (inclusive, 0-indexed)
# these correspond to lines 434 to 628 (1-indexed)
del lines[433:628]

with open(filename, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed professor.py")
