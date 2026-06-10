-- Add submission tracking to grades table
ALTER TABLE grades
ADD COLUMN submitted BOOLEAN DEFAULT FALSE AFTER updated_at,
ADD COLUMN submitted_at DATETIME DEFAULT NULL AFTER submitted,
ADD COLUMN submitted_by INT DEFAULT NULL AFTER submitted_at,
ADD CONSTRAINT fk_grades_submitted_by FOREIGN KEY (submitted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Create a view or table to track period submission status per course/section
CREATE TABLE IF NOT EXISTS grade_submissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    school_id INT NOT NULL,
    course_id INT NOT NULL,
    section_id INT NOT NULL,
    period VARCHAR(30) NOT NULL,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    submitted_by INT NOT NULL,
    locked BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_submission (course_id, period),
    CONSTRAINT fk_submission_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    CONSTRAINT fk_submission_section FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    CONSTRAINT fk_submission_user FOREIGN KEY (submitted_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_submission_school FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE
);
