#!/usr/bin/env python3
"""
Customer API - Application entry point
Minimal initialization file that creates and runs the Flask application
"""

import os
from __init__ import create_app

# Create application instance using the factory function
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    # Run the application
    app.run(debug=debug, host=host, port=port)
