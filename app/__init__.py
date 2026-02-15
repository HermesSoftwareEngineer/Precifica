import os
from datetime import datetime, timedelta, timezone
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity
from config import Config
from app.extensions import db, bcrypt, login_manager, cors, jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)

    # Configurar CORS baseado em variável de ambiente FRONTEND_URL
    frontend_origin = app.config.get('FRONTEND_URL') or os.environ.get('FRONTEND_URL', '*')
    
    # Se frontend_origin for '*', supports_credentials deve ser False
    supports_credentials = True
    if frontend_origin == '*':
        supports_credentials = False

    CORS(
        app,
        origins=[frontend_origin],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        expose_headers=["X-New-Access-Token"],
        supports_credentials=supports_credentials
    )
    app.logger.info(f"CORS configurado com origin: {frontend_origin}")

    @app.after_request
    def refresh_expiring_jwts(response):
        try:
            exp_timestamp = get_jwt()["exp"]
            now = datetime.now(timezone.utc)
            # Renova o token se ele estiver expirando em menos de 1 hora (basicamente toda requisição)
            # Isso garante que a contagem reinicie sempre que houver uso
            target_timestamp = datetime.timestamp(now + timedelta(hours=1))
            if target_timestamp > exp_timestamp:
                access_token = create_access_token(identity=get_jwt_identity())
                response.headers['X-New-Access-Token'] = access_token
        except (RuntimeError, KeyError):
            # Case where there is not a valid JWT. Just return the original response
            return response
        return response

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
