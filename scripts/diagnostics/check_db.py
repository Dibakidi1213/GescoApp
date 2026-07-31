#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

from app import app
from models import db, Section

with app.app_context():
    sections = Section.query.filter_by(name='ELECTRICITE').order_by(Section.level).all()
    print("ELECTRICITE sections:")
    for s in sections:
        print(f"  ID: {s.id}, Name: {s.name}, Level: {s.level}, Class: {s.class_name}")
