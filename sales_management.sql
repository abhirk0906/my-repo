CREATE DATABASE sales_management;
USE sales_management;

CREATE TABLE branches (
branch_id INT AUTO_INCREMENT PRIMARY KEY,
branch_name VARCHAR(100) NOT NULL,
branch_admin_name VARCHAR(100) NOT NULL
);

CREATE TABLE customer_sales (
sale_id INT AUTO_INCREMENT PRIMARY KEY,
branch_id INT,
date DATE,
name VARCHAR(100),
mobile_number VARCHAR(15) UNIQUE,
Product_name VARCHAR(30),
gross_sales DECIMAL(12,2),
received_amount DECIMAL(12,2) DEFAULT 0,
pending_amount DECIMAL(12,2)
GENERATED ALWAYS AS (gross_sales - received_amount) STORED,
status ENUM('open','close') DEFAULT 'open',

FOREIGN KEY (branch_id)
REFERENCES branches(branch_id)
);

CREATE TABLE users(
user_id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(100),
password VARCHAR(255),
branch_id INT,
role ENUM('Super Admin', 'Admin'),
email VARCHAR(255) UNIQUE,

FOREIGN KEY (branch_id)
REFERENCES branches(branch_id)
);

CREATE TABLE payment_splits(
payment_id INT AUTO_INCREMENT PRIMARY KEY,
sale_id INT,
payment_date DATE,
amount_paid DECIMAL(12,2),
payment_method VARCHAR(50),

FOREIGN KEY (sale_id)
REFERENCES customer_sales(sale_id)
);

SHOW TABLES;


DELIMITER $$
CREATE TRIGGER update_received_amount
AFTER INSERT ON payment_splits
FOR EACH ROW
BEGIN
    UPDATE customer_sales
    SET received_amount = (
        SELECT IFNULL(SUM(amount_paid), 0)
        FROM payment_splits
        WHERE sale_id = NEW.sale_id
    )
    WHERE sale_id = NEW.sale_id;
END$$
DELIMITER ;

INSERT INTO branches (branch_id, branch_name, branch_admin_name) VALUES
(1, 'Chennai', 'Arun Kumar'),
(2, 'Bangalore', 'Ravi Shankar'),
(3, 'Hyderabad', 'Suresh Reddy'),
(4, 'Delhi', 'Neha Sharma'),
(5, 'Mumbai', 'Rahul Mehta'),
(6, 'Pune', 'Amit Patil'),
(7, 'Kolkata', 'Subham Ghosh'),
(8, 'Ahmedabad', 'Raj Patel');

USE Sales_Management;

-- 1. Wipe out any existing data in the users table
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- 2. Run your clean insertion query again
INSERT INTO users (username, password, branch_id, role, email) VALUES
('superadmin', 'super123', NULL, 'Super Admin', 'superadmin@company.com'),
('admin_chennai', 'admin123', 1, 'Admin', 'chennai@company.com'),
('admin_bangalore', 'admin123', 2, 'Admin', 'bangalore@company.com'),
('admin_hyderabad', 'admin123', 3, 'Admin', 'hyderabad@company.com'),
('admin_delhi', 'admin123', 4, 'Admin', 'delhi@company.com'),
('admin_mumbai', 'admin123', 5, 'Admin', 'mumbai@company.com'),
('admin_pune', 'admin123', 6, 'Admin', 'pune@company.com'),
('admin_kolkata', 'admin123', 7, 'Admin', 'kolkata@company.com'),
('admin_ahmedabad', 'admin123', 8, 'Admin', 'ahmedabad@company.com');