import os
from flask import Flask
from config import Config
from app.extensions import db, bcrypt, login_manager, cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Configurar CORS baseado em variável de ambiente FRONTEND_ORIGIN
    frontend_origin = os.environ.get('FRONTEND_ORIGIN', '*')
    cors.init_app(
        app,
        origins=[frontend_origin],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        supports_credentials=True
    )
    app.logger.info(f"CORS configurado com origin: {frontend_origin}")

    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.evaluation_routes import evaluation_bp
    from app.routes.bot_routes import bot_bp
    from app.routes.conversation_routes import conversation_bp
    from app.routes.dashboard_routes import dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(bot_bp)
    app.register_blueprint(conversation_bp)
    app.register_blueprint(dashboard_bp)

    return app
