#!/usr/bin/env python
# -*- coding: utf-8 -*-
from app import app, db
from sqlalchemy import text

# Make professor_id nullable
with app.app_context():
    with db.engine.connect() as connection:
        connection.execute(text('ALTER TABLE courses MODIFY COLUMN professor_id INT NULL'))
        connection.commit()
        print('Migration applied: professor_id is now nullable')
