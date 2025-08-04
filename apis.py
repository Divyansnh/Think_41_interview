#!/usr/bin/env python3
"""
APIs module - API endpoints for customer management
Contains all API route definitions and business logic
"""

from flask import request, jsonify, Blueprint, current_app
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
from database import get_db_connection

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api')

def validate_positive_integer(value, param_name):
    """Validate that a parameter is a positive integer"""
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError(f"{param_name} must be a positive integer")
        return int_value
    except (ValueError, TypeError):
        raise ValueError(f"{param_name} must be a valid positive integer")

@api.route('/customers', methods=['GET'])
def list_customers():
    """
    List all customers with pagination support
    Query parameters:
    - page: Page number (default: 1)
    - limit: Number of customers per page (default: 10, max: 100)
    - search: Search term for first_name, last_name, or email
    """
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', current_app.config['DEFAULT_PAGE_SIZE'], type=int)
        search = request.args.get('search', '', type=str).strip()
        
        # Validate parameters
        if page < 1:
            return jsonify({
                'error': 'Invalid page number',
                'message': 'Page number must be 1 or greater',
                'status': 400
            }), 400
            
        if limit < 1 or limit > current_app.config['MAX_PAGE_SIZE']:
            return jsonify({
                'error': 'Invalid limit',
                'message': f'Limit must be between 1 and {current_app.config["MAX_PAGE_SIZE"]}',
                'status': 400
            }), 400
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get database connection
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'error': 'Database Error',
                'message': 'Unable to connect to database',
                'status': 500
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Build query with optional search
        base_query = """
            SELECT id, first_name, last_name, email, age, gender, 
                   state, city, country, timestamp
            FROM users
        """
        count_query = "SELECT COUNT(*) as total FROM users"
        
        params = []
        if search:
            search_condition = """
                WHERE first_name LIKE %s 
                OR last_name LIKE %s 
                OR email LIKE %s
            """
            base_query += search_condition
            count_query += search_condition
            search_param = f"%{search}%"
            params = [search_param, search_param, search_param]
        
        # Get total count
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']
        
        # Get customers with pagination
        query = base_query + " ORDER BY id LIMIT %s OFFSET %s"
        cursor.execute(query, params + [limit, offset])
        customers = cursor.fetchall()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        response = {
            'customers': customers,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            },
            'status': 200
        }
        
        if search:
            response['search'] = search
            
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in list_customers: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An error occurred while fetching customers',
            'status': 500
        }), 500
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

@api.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    """
    Get specific customer details including order count
    Path parameter:
    - customer_id: The ID of the customer
    """
    try:
        # Validate customer_id
        if customer_id <= 0:
            return jsonify({
                'error': 'Invalid Customer ID',
                'message': 'Customer ID must be a positive integer',
                'status': 400
            }), 400
        
        # Get database connection
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'error': 'Database Error',
                'message': 'Unable to connect to database',
                'status': 500
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get customer details
        customer_query = """
            SELECT id, first_name, last_name, email, age, gender,
                   state, address, postal_code, city, country,
                   latitude, longitude, search_term, timestamp
            FROM users 
            WHERE id = %s
        """
        cursor.execute(customer_query, (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            return jsonify({
                'error': 'Customer Not Found',
                'message': f'Customer with ID {customer_id} does not exist',
                'status': 404
            }), 404
        
        # Get order count and statistics
        order_stats_query = """
            SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_orders,
                COUNT(CASE WHEN status = 'returned' THEN 1 END) as returned_orders,
                COUNT(CASE WHEN status = 'shipped' THEN 1 END) as shipped_orders,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
                SUM(num_of_item) as total_items,
                MIN(created_at) as first_order_date,
                MAX(created_at) as last_order_date
            FROM orders 
            WHERE user_id = %s
        """
        cursor.execute(order_stats_query, (customer_id,))
        order_stats = cursor.fetchone()
        
        # Format the response
        response = {
            'customer': {
                'id': customer['id'],
                'first_name': customer['first_name'],
                'last_name': customer['last_name'],
                'full_name': f"{customer['first_name']} {customer['last_name']}",
                'email': customer['email'],
                'age': customer['age'],
                'gender': customer['gender'],
                'location': {
                    'address': customer['address'],
                    'city': customer['city'],
                    'state': customer['state'],
                    'postal_code': customer['postal_code'],
                    'country': customer['country'],
                    'coordinates': {
                        'latitude': float(customer['latitude']) if customer['latitude'] else None,
                        'longitude': float(customer['longitude']) if customer['longitude'] else None
                    }
                },
                'search_term': customer['search_term'],
                'registered_at': customer['timestamp'].isoformat() if customer['timestamp'] and hasattr(customer['timestamp'], 'isoformat') else str(customer['timestamp']) if customer['timestamp'] else None
            },
            'order_summary': {
                'total_orders': order_stats['total_orders'],
                'orders_by_status': {
                    'delivered': order_stats['delivered_orders'],
                    'returned': order_stats['returned_orders'],
                    'shipped': order_stats['shipped_orders'],
                    'pending': order_stats['pending_orders']
                },
                'total_items_purchased': order_stats['total_items'] or 0,
                'first_order_date': order_stats['first_order_date'].isoformat() if order_stats['first_order_date'] and hasattr(order_stats['first_order_date'], 'isoformat') else str(order_stats['first_order_date']) if order_stats['first_order_date'] else None,
                'last_order_date': order_stats['last_order_date'].isoformat() if order_stats['last_order_date'] and hasattr(order_stats['last_order_date'], 'isoformat') else str(order_stats['last_order_date']) if order_stats['last_order_date'] else None
            },
            'status': 200
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in get_customer_details: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An error occurred while fetching customer details',
            'status': 500
        }), 500
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

@api.route('/customers/<int:customer_id>/orders', methods=['GET'])
def get_customer_orders(customer_id):
    """
    Get all orders for a specific customer
    Path parameter:
    - customer_id: The ID of the customer
    Query parameters:
    - page: Page number (default: 1)
    - limit: Number of orders per page (default: 10, max: 100)
    - status: Filter by order status (optional)
    """
    try:
        # Validate customer_id
        if customer_id <= 0:
            return jsonify({
                'error': 'Invalid Customer ID',
                'message': 'Customer ID must be a positive integer',
                'status': 400
            }), 400
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', current_app.config['DEFAULT_PAGE_SIZE'], type=int)
        status_filter = request.args.get('status', '', type=str).strip().lower()
        
        # Validate parameters
        if page < 1:
            return jsonify({
                'error': 'Invalid page number',
                'message': 'Page number must be 1 or greater',
                'status': 400
            }), 400
            
        if limit < 1 or limit > current_app.config['MAX_PAGE_SIZE']:
            return jsonify({
                'error': 'Invalid limit',
                'message': f'Limit must be between 1 and {current_app.config["MAX_PAGE_SIZE"]}',
                'status': 400
            }), 400
        
        # Get database connection
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'error': 'Database Error',
                'message': 'Unable to connect to database',
                'status': 500
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # First, verify customer exists
        cursor.execute("SELECT id, first_name, last_name FROM users WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            return jsonify({
                'error': 'Customer Not Found',
                'message': f'Customer with ID {customer_id} does not exist',
                'status': 404
            }), 404
        
        # Build query with optional status filter
        base_query = """
            SELECT order_id, user_id, status, gender, created_at, 
                   returned_at, shipped_at, delivered_at, num_of_item
            FROM orders
            WHERE user_id = %s
        """
        count_query = "SELECT COUNT(*) as total FROM orders WHERE user_id = %s"
        
        params = [customer_id]
        if status_filter:
            base_query += " AND LOWER(status) = %s"
            count_query += " AND LOWER(status) = %s"
            params.append(status_filter)
        
        # Get total count
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get orders with pagination
        query = base_query + " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [limit, offset])
        orders = cursor.fetchall()
        
        # Format orders response
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'order_id': order['order_id'],
                'user_id': order['user_id'],
                'status': order['status'],
                'gender': order['gender'],
                'num_of_items': order['num_of_item'],
                'created_at': order['created_at'].isoformat() if order['created_at'] and hasattr(order['created_at'], 'isoformat') else str(order['created_at']) if order['created_at'] else None,
                'returned_at': order['returned_at'].isoformat() if order['returned_at'] and hasattr(order['returned_at'], 'isoformat') else str(order['returned_at']) if order['returned_at'] else None,
                'shipped_at': order['shipped_at'].isoformat() if order['shipped_at'] and hasattr(order['shipped_at'], 'isoformat') else str(order['shipped_at']) if order['shipped_at'] else None,
                'delivered_at': order['delivered_at'].isoformat() if order['delivered_at'] and hasattr(order['delivered_at'], 'isoformat') else str(order['delivered_at']) if order['delivered_at'] else None
            })
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        response = {
            'customer': {
                'id': customer['id'],
                'name': f"{customer['first_name']} {customer['last_name']}"
            },
            'orders': formatted_orders,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            },
            'status': 200
        }
        
        if status_filter:
            response['filter'] = {'status': status_filter}
            
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in get_customer_orders: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An error occurred while fetching customer orders',
            'status': 500
        }), 500
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

@api.route('/orders/<int:order_id>', methods=['GET'])
def get_order_details(order_id):
    """
    Get specific order details
    Path parameter:
    - order_id: The ID of the order
    """
    try:
        # Validate order_id
        if order_id <= 0:
            return jsonify({
                'error': 'Invalid Order ID',
                'message': 'Order ID must be a positive integer',
                'status': 400
            }), 400
        
        # Get database connection
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'error': 'Database Error',
                'message': 'Unable to connect to database',
                'status': 500
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get order details with customer information
        order_query = """
            SELECT o.order_id, o.user_id, o.status, o.gender, o.created_at,
                   o.returned_at, o.shipped_at, o.delivered_at, o.num_of_item,
                   u.first_name, u.last_name, u.email, u.age, u.city, u.state, u.country
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.order_id = %s
        """
        cursor.execute(order_query, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return jsonify({
                'error': 'Order Not Found',
                'message': f'Order with ID {order_id} does not exist',
                'status': 404
            }), 404
        
        # Format the response
        response = {
            'order': {
                'order_id': order['order_id'],
                'user_id': order['user_id'],
                'status': order['status'],
                'gender': order['gender'],
                'num_of_items': order['num_of_item'],
                'timestamps': {
                    'created_at': order['created_at'].isoformat() if order['created_at'] and hasattr(order['created_at'], 'isoformat') else str(order['created_at']) if order['created_at'] else None,
                    'returned_at': order['returned_at'].isoformat() if order['returned_at'] and hasattr(order['returned_at'], 'isoformat') else str(order['returned_at']) if order['returned_at'] else None,
                    'shipped_at': order['shipped_at'].isoformat() if order['shipped_at'] and hasattr(order['shipped_at'], 'isoformat') else str(order['shipped_at']) if order['shipped_at'] else None,
                    'delivered_at': order['delivered_at'].isoformat() if order['delivered_at'] and hasattr(order['delivered_at'], 'isoformat') else str(order['delivered_at']) if order['delivered_at'] else None
                }
            },
            'customer': {
                'id': order['user_id'],
                'first_name': order['first_name'],
                'last_name': order['last_name'],
                'full_name': f"{order['first_name']} {order['last_name']}" if order['first_name'] and order['last_name'] else None,
                'email': order['email'],
                'age': order['age'],
                'location': {
                    'city': order['city'],
                    'state': order['state'],
                    'country': order['country']
                }
            },
            'status': 200
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in get_order_details: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An error occurred while fetching order details',
            'status': 500
        }), 500
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        connection = get_db_connection()
        if connection:
            connection.close()
            db_status = "connected"
        else:
            db_status = "disconnected"
            
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'timestamp': datetime.now().isoformat(),
            'version': current_app.config['API_VERSION']
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
