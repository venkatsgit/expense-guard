CREATE DATABASE IF NOT EXISTS expense_insights;

USE expense_insights;

CREATE TABLE IF NOT EXISTS `expenses` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` VARCHAR(45) NOT NULL,
  `file_id` INT NOT NULL,
  `expense` DECIMAL(7,2) NOT NULL,
  `currency_code` VARCHAR(45) NOT NULL,
  `description` VARCHAR(45) NOT NULL,
  `category` VARCHAR(45) DEFAULT NULL,
  `date` DATE NOT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_unique_expense` (`user_id`,`expense`,`currency_code`,`description`)
);

CREATE TABLE IF NOT EXISTS `upload_history` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` VARCHAR(45) NOT NULL,
  `file_name` VARCHAR(45) NOT NULL,
  `status` VARCHAR(45) NOT NULL,
  `message` VARCHAR(45) DEFAULT NULL,
  `uploaded_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `users` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);