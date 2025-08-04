#!/usr/bin/env python3
"""
Database module - Database connection and configuration
Handles MySQL database connections using Flask app configuration
"""

import mysql.connector
from mysql.connector import Error
import logging
import os
from flask import current_app, has_app_context

# Configure logging
logger = logging.getLogger(__name__)

def get_db_connection():
    """Create and return a database connection using environment variables"""
    try:
        # Use environment variables directly for simplicity and reliability
        db_config = _get_env_db_config()
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return None

def _get_env_db_config():
    """Get database configuration from environment variables"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'e-commerce'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }

def test_connection():
    """Test database connection and return status"""
    try:
        connection = get_db_connection()
        if connection and connection.is_connected():
            connection.close()
            return True, "Database connection successful"
        else:
            return False, "Failed to connect to database"
    except Exception as e:
        return False, f"Database connection error: {str(e)}"
