CREATE TABLE orders (
    order_id INT,
    user_id INT,
    status VARCHAR(50),
    gender CHAR(1),
    created_at DATETIME,
    returned_at DATETIME NULL,
    shipped_at DATETIME NULL,
    delivered_at DATETIME NULL,
    num_of_item INT
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
