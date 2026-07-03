-- Question 4: Relational Databases
-- Schema, sample data, and the answer query.
-- Run with: sqlite3 school.db < school.sql

.headers on
.mode column

-- ---------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------

CREATE TABLE students (
    student_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    email         TEXT UNIQUE,
    date_of_birth DATE
);

CREATE TABLE courses (
    course_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT NOT NULL,
    course_code TEXT UNIQUE
);

-- Junction table: models the many-to-many relationship between
-- students and courses. UNIQUE(student_id, course_id) prevents
-- the same student enrolling in the same course twice.
CREATE TABLE enrollments (
    enrollment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    course_id       INTEGER NOT NULL,
    enrollment_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id)  REFERENCES courses(course_id),
    UNIQUE (student_id, course_id)
);

-- ---------------------------------------------------------------
-- Sample data
-- ---------------------------------------------------------------

INSERT INTO students (first_name, last_name, email) VALUES
('Winstone', 'Kamau',  'wanjiku@school.ac.ke'),
('Brian',   'Otieno', 'brian@school.ac.ke'),
('Amina',   'Hassan', 'amina@school.ac.ke');

INSERT INTO courses (course_name, course_code) VALUES
('Introduction to Programming', 'CS101'),
('Database Systems',            'CS202');

-- Wanjiku and Amina take Intro to Programming; Brian takes Database Systems.
-- Brian should NOT appear in the answer query result.
INSERT INTO enrollments (student_id, course_id, enrollment_date) VALUES
(1, 1, '2026-01-10'),
(3, 1, '2026-01-11'),
(2, 2, '2026-01-10');

-- ---------------------------------------------------------------
-- Answer query: all students enrolled in "Introduction to Programming"
-- ---------------------------------------------------------------

SELECT s.student_id, s.first_name, s.last_name
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c     ON e.course_id  = c.course_id
WHERE c.course_name = 'Introduction to Programming';
