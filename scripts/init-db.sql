-- TEAPS v5 Database Initialization Script
-- This file is automatically executed when MySQL container starts for the first time

USE teaps_v5;

-- Create users table if not exists (in case ORM fails)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    name_tc VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('employee', 'manager', 'admin', 'super_admin') DEFAULT 'employee',
    department_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- Create departments table if not exists
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name_tc VARCHAR(200) NOT NULL,
    name_en VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    manager_id INT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- Create attendance_records table if not exists
CREATE TABLE IF NOT EXISTS attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    date DATE NOT NULL,
    check_in_time TIMESTAMP NULL,
    check_out_time TIMESTAMP NULL,
    break_duration_minutes INT DEFAULT 0,
    check_in_location VARCHAR(255),
    check_out_location VARCHAR(255),
    scheduled_hours DECIMAL(3,1) DEFAULT 8.0,
    actual_hours DECIMAL(4,2) DEFAULT 0.0,
    status ENUM('pending', 'approved', 'rejected', 'late', 'early_leave', 'absent') DEFAULT 'pending',
    late_minutes INT DEFAULT 0,
    early_leave_minutes INT DEFAULT 0,
    manager_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_date (user_id, date),
    INDEX idx_status (status),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create payroll_records table if not exists
CREATE TABLE IF NOT EXISTS payroll_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    base_salary DECIMAL(10,2) NOT NULL,
    attendance_days INT DEFAULT 0,
    scheduled_days INT DEFAULT 0,
    overtime_hours DECIMAL(5,2) DEFAULT 0.0,
    overtime_rate DECIMAL(3,2) DEFAULT 1.5,
    overtime_pay DECIMAL(10,2) DEFAULT 0.0,
    bonus DECIMAL(10,2) DEFAULT 0.0,
    allowance DECIMAL(10,2) DEFAULT 0.0,
    deduction_absent DECIMAL(10,2) DEFAULT 0.0,
    deduction_late DECIMAL(10,2) DEFAULT 0.0,
    deduction_other DECIMAL(10,2) DEFAULT 0.0,
    tax_deduction DECIMAL(10,2) DEFAULT 0.0,
    social_security DECIMAL(10,2) DEFAULT 0.0,
    gross_pay DECIMAL(10,2) DEFAULT 0.0,
    net_pay DECIMAL(10,2) DEFAULT 0.0,
    status ENUM('pending', 'approved', 'paid', 'rejected', 'hold') DEFAULT 'pending',
    approved_by INT,
    approved_at TIMESTAMP NULL,
    paid_at TIMESTAMP NULL,
    notes TEXT,
    manager_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_period (user_id, period_start),
    INDEX idx_status (status),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- Create a demo admin user (password: admin123, change immediately!)
INSERT INTO users (employee_id, name_tc, name_en, email, password_hash, role) 
VALUES ('ADMIN001', '系統管理員', 'System Administrator', 'admin@teaps.local', 
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILp92S.0i', 
        'super_admin')
ON DUPLICATE KEY UPDATE name_tc = VALUES(name_tc);

-- Create a demo department
INSERT INTO departments (code, name_tc, name_en) 
VALUES ('HR001', '人力資源部', 'Human Resources Department')
ON DUPLICATE KEY UPDATE name_tc = VALUES(name_tc);
