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
