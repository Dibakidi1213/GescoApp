ALTER TABLE students
  ADD COLUMN place_of_birth VARCHAR(120) NULL AFTER last_name,
  ADD COLUMN father_name VARCHAR(120) NULL AFTER gender,
  ADD COLUMN mother_name VARCHAR(120) NULL AFTER father_name,
  ADD COLUMN parent_phone VARCHAR(50) NULL AFTER mother_name,
  ADD COLUMN serial_number VARCHAR(80) NULL AFTER parent_phone;
