import os
from flask import Flask
from config import Config
from extensions import db
from database import init_db
from routes import initialize_routes
from services import AppService

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    
    # Create an instance of AppService and initialize clients
    service = AppService(app)
    service.init_clients(app.config['PROJECT_ID'], app.config['LOCATION'])

    # Initialize routes
    initialize_routes(app, service)

    # Create database tables
    with app.app_context():
        init_db(app)

    return app

app = create_app()

if __name__ == '__main__':
    os.makedirs(app.config['VIDEO_DIR'], exist_ok=True)
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
