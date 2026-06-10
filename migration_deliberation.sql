ALTER TABLE bulletin_branches ADD COLUMN category VARCHAR(30) DEFAULT 'general';

CREATE TABLE deliberation_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,
    academic_year VARCHAR(30) NOT NULL,
    level_group VARCHAR(50) NOT NULL,
    min_percentage_auto NUMERIC(5, 2) DEFAULT 50,
    max_echecs_auto INTEGER DEFAULT 0,
    min_percentage_repechage NUMERIC(5, 2) DEFAULT 50,
    max_echecs_repechage INTEGER DEFAULT 0,
    min_score_specific_branch NUMERIC(5, 2) DEFAULT 30,
    min_score_option_branch NUMERIC(5, 2) DEFAULT 35,
    min_percentage_redoublement NUMERIC(5, 2) DEFAULT 45,
    require_good_conduct BOOLEAN DEFAULT 1,
    max_mauvaise_conduite INTEGER DEFAULT 2,
    min_percentage_exclusion NUMERIC(5, 2) DEFAULT 45,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(school_id) REFERENCES schools(id)
);

CREATE TABLE deliberation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    academic_year VARCHAR(30) NOT NULL,
    period VARCHAR(30) NOT NULL,
    total_percentage NUMERIC(5, 2) NOT NULL,
    echecs_count INTEGER DEFAULT 0,
    decision VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(school_id) REFERENCES schools(id),
    FOREIGN KEY(student_id) REFERENCES students(id),
    CONSTRAINT unique_student_deliberation UNIQUE (student_id, academic_year, period)
);
