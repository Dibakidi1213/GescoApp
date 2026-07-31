-- Migration: Make professor_id nullable in courses table
ALTER TABLE courses MODIFY COLUMN professor_id INT NULL;
