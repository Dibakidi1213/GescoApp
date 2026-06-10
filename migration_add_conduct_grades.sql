CREATE TABLE conduct_grades (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    academic_year VARCHAR(30),
    period VARCHAR(30) NOT NULL,
    value VARCHAR(10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(school_id) REFERENCES schools (id),
    FOREIGN KEY(student_id) REFERENCES students (id),
    CONSTRAINT unique_student_conduct UNIQUE (student_id, academic_year, period)
);
