-- Migration SQL for adding school slug support
ALTER TABLE schools
  ADD COLUMN slug VARCHAR(120) NULL;

ALTER TABLE schools
  ADD UNIQUE INDEX idx_schools_slug (slug);
