-- Script SQL para criar o banco de dados
CREATE DATABASE dbname;
USE dbname;

CREATE TABLE players (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    stats JSON NOT NULL
);

CREATE TABLE demos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    processed BOOLEAN DEFAULT FALSE
);