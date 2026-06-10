-- Migration: Make section_id nullable in courses table
-- This allows importing courses without assigning a section first
-- After import, sections can be assigned through the UI

ALTER TABLE courses MODIFY section_id INT NULL;
