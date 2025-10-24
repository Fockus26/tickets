from flask import Flask
from config import Config
from extensions import db, api
from routes.api_routes import register_api_routes
from routes.web_routes import web_bp
from routes.auth_routes import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    api.init_app(app)

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)

    # Registrar recursos REST
    register_api_routes(api)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run('localhost', 8000, debug=True)
