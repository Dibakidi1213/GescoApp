#!/usr/bin/env python3
"""Analyser le template pour trouver les erreurs de syntaxe JavaScript"""

import re
from pathlib import Path

template_path = Path('templates/admin/bulletins.html')
content = template_path.read_text(encoding='utf-8')

# Chercher des problèmes potentiels :
# 1. Accolades déséquilibrées dans les templates literals
# 2. Guillemets non fermés
# 3. Expressions Jinja2 mal formées

# Extraire juste la partie JavaScript
lines = content.split('\n')

# Chercher les erreurs
issues = []

# Vérifier les accolades dans les expressions template literals
for i, line in enumerate(lines, 1):
    # Vérifier si la ligne contient des expressions ternaires mal formées
    if '${' in line and ('?' in line and ':' not in line):
        if '};' not in line:  # Voir si la closure est sur la même ligne
            issues.append(f"Line {i}: Expression ternaire potentiellement non fermée: {line.strip()}")
    
    # Vérifier les guillemets non fermés dans les strings
    # Compter les guillemets simples non échappés
    if "'" in line and 'class=' not in line:
        single_quotes = line.count("'") - line.count("\\'")
        if single_quotes % 2 != 0:
            issues.append(f"Line {i}: Nombre impair de guillemets simples: {line.strip()}")

    # Vérifier les expressions Jinja2 mal formées
    if '{{' in line:
        open_count = line.count('{{')
        close_count = line.count('}}')
        if open_count != close_count:
            issues.append(f"Line {i}: Jinja2 non équilibré - {open_count} {{ et {close_count} }}: {line.strip()}")

    # Chercher les template literals mal fermées
    if '`' in line:
        backtick_count = line.count('`')
        if backtick_count % 2 != 0:
            issues.append(f"Line {i}: Nombre impair de backticks (template literal): {line.strip()}")

# Vérifier les accolades { } dans le JavaScript
print("🔍 Analyse JavaScript du template bulletins.html\n")

if issues:
    print(f"⚠️  {len(issues)} problèmes potentiels trouvés:\n")
    for issue in issues[:20]:  # Afficher max 20
        print(f"  {issue}")
else:
    print("✅ Aucun problème de syntaxe basique détecté")

# Vérifier les expressions ternaires avec des guillemets simples dans des template literals
print("\n🔍 Cherchant des expressions ternaires complexes...\n")
ternary_issues = []
for i, line in enumerate(lines, 1):
    if '${' in line and '?' in line:
        # Ceci contient une expression ternaire
        match = re.search(r'\$\{([^}]+)\}', line)
        if match:
            expr = match.group(1)
            # Vérifier si elle contient des guillemets simples
            if "'" in expr and ('<' in expr or '>' in expr or 'colspan' in expr):
                ternary_issues.append(f"Line {i}: Expression ternaire avec HTML: {line.strip()}")

if ternary_issues:
    print(f"⚠️  {len(ternary_issues)} expressions ternaires complexes trouvées:\n")
    for issue in ternary_issues[:10]:
        print(f"  {issue}")
else:
    print("✅ Pas de problèmes avec les expressions ternaires")

print("\n💡 Conseil: La véritable erreur peut être dans du HTML rendu mal formé")
print("   Visitez: http://localhost:5000/admin/bulletins-config?school_id=1")
print("   Ouvrez F12 → Console et vérifiez le message d'erreur complet")
