import ast
try:
    with open('routes/admin.py', 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    print('Syntax is valid')
except SyntaxError as e:
    print(f'Syntax error: {e}')
    print(f'Line {e.lineno}: {e.text}')
except Exception as e:
    print(f'Other error: {e}')