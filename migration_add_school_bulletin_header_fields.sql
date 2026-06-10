-- Add school-level bulletin header fields
ALTER TABLE schools ADD COLUMN city VARCHAR(120) NULL;
ALTER TABLE schools ADD COLUMN commune VARCHAR(120) NULL;
ALTER TABLE schools ADD COLUMN bulletin_school_name VARCHAR(255) NULL;
ALTER TABLE schools ADD COLUMN school_code VARCHAR(50) NULL;
