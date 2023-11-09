CREATE DATABASE `workflow` CHARACTER SET utf8mb4;

CREATE USER root IDENTIFIED BY 'pwd123456';
GRANT All privileges ON *.* TO root@'%';
flush privileges;
