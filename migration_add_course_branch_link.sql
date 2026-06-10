-- Add branch_id column to courses table to link courses with bulletin branches
ALTER TABLE courses
ADD COLUMN branch_id INT DEFAULT NULL AFTER professor_id,
ADD CONSTRAINT fk_courses_branch FOREIGN KEY (branch_id) REFERENCES bulletin_branches(id) ON DELETE SET NULL;
