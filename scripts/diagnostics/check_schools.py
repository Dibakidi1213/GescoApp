from models import db, School
db.create_all()
schools = School.query.all()
print('Écoles dans la DB:')
for s in schools:
    print(f'ID: {s.id}, Nom: {s.name}, Slug: {s.slug}, Actif: {s.is_active}')