#!/usr/bin/env python3
"""
Configuration module - Application configuration settings
Contains different configuration classes for different environments
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'customer_db')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_CHARSET = 'utf8mb4'
    DB_COLLATION = 'utf8mb4_unicode_ci'
    
    # API Configuration
    API_VERSION = '1.0.0'
    API_TITLE = 'Customer API'
    
    # Pagination Configuration
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    
    # CORS Configuration
    CORS_ORIGINS = ["*"]
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization"]
    
    @property
    def DATABASE_CONFIG(self):
        """Return database configuration dictionary"""
        return {
            'host': self.DB_HOST,
            'database': self.DB_NAME,
            'user': self.DB_USER,
            'password': self.DB_PASSWORD,
            'charset': self.DB_CHARSET,
            'collation': self.DB_COLLATION
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    # Use a separate test database
    DB_NAME = os.getenv('TEST_DB_NAME', 'customer_db_test')

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # In production, these should be set via environment variables
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # More restrictive CORS for production
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization"""
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
