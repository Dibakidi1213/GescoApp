-- Migration: Add IGE number to bulletin_configs
-- Description: Adds a unique IGE number for each bulletin configuration
-- Format: IGE/[SECTION]/[NUMERO] (e.g., IGE/PS/026)

-- Add ige_number column to bulletin_configs table
ALTER TABLE bulletin_configs 
ADD COLUMN ige_number VARCHAR(50) NULL UNIQUE AFTER level;

-- Add index for faster lookups
CREATE INDEX idx_ige_number ON bulletin_configs(ige_number);

-- Add index for section_id to help with IGE generation
CREATE INDEX idx_config_section ON bulletin_configs(school_id, section_id);

COMMIT;
