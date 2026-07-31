ALTER TABLE bulletin_branches
  ADD COLUMN domain VARCHAR(120) DEFAULT '' NULL AFTER config_id,
  ADD COLUMN subdomain VARCHAR(120) DEFAULT '' NULL AFTER domain;