# Customer API

A REST API for managing customer data with order statistics, built with Flask and MySQL.

## Features

- **List all customers** with pagination and search functionality
- **Get specific customer details** including comprehensive order statistics
- **Proper JSON response format** with consistent error handling
- **Robust error handling** for invalid IDs, missing customers, and database issues
- **Health check endpoint** for monitoring
- **Environment-based configuration** for different deployment environments

## API Endpoints

### 1. List All Customers
```
GET /api/customers
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Number of customers per page (default: 10, max: 100)
- `search` (optional): Search term for first_name, last_name, or email

**Example Request:**
```bash
curl "http://localhost:5000/api/customers?page=1&limit=5&search=john"
```

**Example Response:**
```json
{
  "customers": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "age": 30,
      "gender": "M",
      "state": "CA",
      "city": "Los Angeles",
      "country": "USA",
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 5,
    "total_count": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "search": "john",
  "status": 200
}
```

### 2. Get Customer Details
```
GET /api/customers/{customer_id}
```

**Path Parameters:**
- `customer_id`: The ID of the customer (must be a positive integer)

**Example Request:**
```bash
curl "http://localhost:5000/api/customers/1"
```

**Example Response:**
```json
{
  "customer": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "age": 30,
    "gender": "M",
    "location": {
      "address": "123 Main St",
      "city": "Los Angeles",
      "state": "CA",
      "postal_code": "90210",
      "country": "USA",
      "coordinates": {
        "latitude": 34.0522,
        "longitude": -118.2437
      }
    },
    "search_term": "electronics",
    "registered_at": "2024-01-15T10:30:00"
  },
  "order_summary": {
    "total_orders": 5,
    "orders_by_status": {
      "delivered": 3,
      "returned": 1,
      "shipped": 1,
      "pending": 0
    },
    "total_items_purchased": 12,
    "first_order_date": "2024-01-20T14:30:00",
    "last_order_date": "2024-03-15T09:45:00"
  },
  "status": 200
}
```

### 3. Health Check
```
GET /api/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-08-04T08:59:00",
  "version": "1.0.0"
}
```

## Error Handling

The API returns consistent error responses with appropriate HTTP status codes:

### Customer Not Found (404)
```json
{
  "error": "Customer Not Found",
  "message": "Customer with ID 999 does not exist",
  "status": 404
}
```

### Invalid Parameters (400)
```json
{
  "error": "Invalid Customer ID",
  "message": "Customer ID must be a positive integer",
  "status": 400
}
```

### Database Error (500)
```json
{
  "error": "Database Error",
  "message": "Unable to connect to database",
  "status": 500
}
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd Think_41_interview
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
1. Create a MySQL database:
```sql
CREATE DATABASE customer_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Import the schema:
```bash
mysql -u root -p customer_db < users.sql
mysql -u root -p customer_db < orders.sql
```

### 5. Environment Configuration
1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your database credentials:
```
DB_HOST=localhost
DB_NAME=customer_db
DB_USER=root
DB_PASSWORD=your_password_here
```

### 6. Run the Application
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Production Deployment

For production deployment, use Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Database Schema

### Users Table
- `id`: Primary key
- `first_name`, `last_name`: Customer name
- `email`: Customer email address
- `age`: Customer age
- `gender`: Customer gender (M/F)
- `state`, `city`, `country`: Location information
- `address`, `postal_code`: Detailed address
- `latitude`, `longitude`: Geographic coordinates
- `search_term`: Customer search preferences
- `timestamp`: Registration timestamp

### Orders Table
- `order_id`: Primary key
- `user_id`: Foreign key to users table
- `status`: Order status (pending, shipped, delivered, returned)
- `gender`: Customer gender (denormalized)
- `created_at`: Order creation timestamp
- `returned_at`, `shipped_at`, `delivered_at`: Status timestamps
- `num_of_item`: Number of items in order

## Testing

Test the API endpoints using curl or any HTTP client:

```bash
# List customers
curl "http://localhost:5000/api/customers"

# Get customer details
curl "http://localhost:5000/api/customers/1"

# Search customers
curl "http://localhost:5000/api/customers?search=john&limit=5"

# Health check
curl "http://localhost:5000/api/health"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
