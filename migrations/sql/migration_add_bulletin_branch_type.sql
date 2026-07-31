-- Add type column to bulletin_branches table
ALTER TABLE bulletin_branches ADD COLUMN type VARCHAR(20) DEFAULT 'branch';

-- Update existing rows based on content
-- If domain is set and subdomain is empty, it's a domain
UPDATE bulletin_branches SET type = 'domain' WHERE domain IS NOT NULL AND domain != '' AND (subdomain IS NULL OR subdomain = '') AND (name IS NULL OR name = '');

-- If subdomain is set, it's a subdomain
UPDATE bulletin_branches SET type = 'subdomain' WHERE subdomain IS NOT NULL AND subdomain != '' AND (name IS NULL OR name = '');

-- Otherwise it's a branch (default)
UPDATE bulletin_branches SET type = 'branch' WHERE type = 'domain' AND name IS NOT NULL AND name != '';
