#!/usr/bin/env python3
"""
Application package initialization
Creates and configures the Flask application with proper configuration loading
"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os

def create_app(config_name=None):
    """
    Application factory function
    Creates and configures Flask application instance
    
    Args:
        config_name (str): Configuration environment name ('development', 'testing', 'production')
    
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO if not app.config['DEBUG'] else logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": app.config['CORS_METHODS'],
            "allow_headers": app.config['CORS_HEADERS']
        }
    })
    
    # Register blueprints
    from apis import api
    app.register_blueprint(api)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register root endpoint
    register_root_endpoint(app)
    
    # Initialize configuration-specific settings
    if hasattr(config[config_name], 'init_app'):
        config[config_name].init_app(app)
    
    return app

def register_error_handlers(app):
    """Register application error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status': 404
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors"""
        return jsonify({
            'error': 'Bad Request',
            'message': 'Invalid request parameters',
            'status': 400
        }), 400

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status': 500
        }), 500

def register_root_endpoint(app):
    """Register the root endpoint with API documentation"""
    
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with API information"""
        return jsonify({
            'message': app.config['API_TITLE'],
            'version': app.config['API_VERSION'],
            'environment': os.getenv('FLASK_ENV', 'development'),
            'endpoints': {
                'list_customers': '/api/customers',
                'get_customer': '/api/customers/<id>',
                'health_check': '/api/health'
            },
            'documentation': {
                'list_customers': {
                    'method': 'GET',
                    'parameters': {
                        'page': f'Page number (default: 1)',
                        'limit': f'Items per page (default: {app.config["DEFAULT_PAGE_SIZE"]}, max: {app.config["MAX_PAGE_SIZE"]})',
                        'search': 'Search in first_name, last_name, or email'
                    }
                },
                'get_customer': {
                    'method': 'GET',
                    'description': 'Get customer details with order statistics'
                }
            }
        }), 200
