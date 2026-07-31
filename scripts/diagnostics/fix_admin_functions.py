import re

with open('routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match function definitions in admin_bp routes
pattern = r'(@admin_bp\.route.*?)\n@login_required\n(def \w+\([^)]*)\):'
matches = re.findall(pattern, content, re.MULTILINE)

print('Functions to modify:')
for match in matches:
    print(match[1])