import re

# Lire le template
with open('templates/admin/bulletins.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extraire la section <script>
script_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
if not script_match:
    print("❌ Aucune balise <script> trouvée!")
    exit(1)

script_content = script_match.group(1)

# Vérifier les apostrophes problématiques
problematic_apostrophes = re.findall(r"'[^']*\\\'[^']*'", script_content)
if problematic_apostrophes:
    print("⚠️ Apostrophes échappées trouvées:")
    for match in problematic_apostrophes[:5]:
        print(f"  {match}")
else:
    print("✓ Pas d'apostrophes échappées problématiques")

# Vérifier les guillemets mal équilibrés
opening_quotes = script_content.count('{')
closing_quotes = script_content.count('}')
print(f"\n✓ Accolades: {opening_quotes} '{' et {closing_quotes} '}'")
if opening_quotes != closing_quotes:
    print(f"  ⚠️ INÉGAL!")

# Chercher les erreurs de syntaxe communes
if "const DEFAULT_BRANCHES = [" in script_content:
    print("✓ DEFAULT_BRANCHES défini")
    
if "function loadLevels" in script_content:
    print("✓ fonction loadLevels définie")
else:
    print("❌ fonction loadLevels NOT FOUND!")

if "ADMIN_API_PREFIX" in script_content:
    print("✓ ADMIN_API_PREFIX défini")

print("\n✅ Validation complète")
