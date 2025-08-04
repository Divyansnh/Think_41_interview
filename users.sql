CREATE TABLE users (
  id INT PRIMARY KEY,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255),
  age INT,
  gender CHAR(1),
  state VARCHAR(100),
  address VARCHAR(255),
  postal_code VARCHAR(20),
  city VARCHAR(100),
  country VARCHAR(100),
  latitude DECIMAL(10,7),
  longitude DECIMAL(11,8),
  search_term VARCHAR(100),
  timestamp DATETIME(6)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;