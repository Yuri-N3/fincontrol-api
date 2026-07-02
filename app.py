from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from config import Config
from database import db
from models import Meta, Usuario
from routes.auth import auth_bp
from routes.finance import finance_bp
from routes.reports import reports_bp
from routes.users import users_bp
from services.crud_service import ValidationError


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(reports_bp)

    @app.errorhandler(ValidationError)
    def validation_error(error):
        return jsonify({"erro": str(error), "status": 400}), 400

    @app.errorhandler(IntegrityError)
    def integrity_error(error):
        db.session.rollback()
        return jsonify({"erro": "Dados violam restricoes do banco", "status": 409}), 409

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify({"erro": error.description, "status": error.code}), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        db.session.rollback()
        if app.debug:
            raise error
        return jsonify({"erro": "Erro interno do servidor", "status": 500}), 500

    swagger_ui = get_swaggerui_blueprint(
        "/docs",
        "/swagger/openapi.yaml",
        config={"app_name": "FinControl API"},
    )
    app.register_blueprint(swagger_ui, url_prefix="/docs")

    @app.get("/")
    def health():
        return jsonify({"app": "FinControl API", "status": "online"})

    @app.get("/swagger/openapi.yaml")
    def openapi():
        return send_from_directory("swagger", "openapi.yaml")

    with app.app_context():
        db.create_all()
        ensure_schema()

    return app


def ensure_schema():
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    if "usuarios" in table_names:
        user_columns = {column["name"] for column in inspector.get_columns("usuarios")}
        user_migrations = []
        if "renda_mensal" not in user_columns:
            user_migrations.append("ALTER TABLE usuarios ADD COLUMN renda_mensal FLOAT DEFAULT 0")
        if "objetivo" not in user_columns:
            user_migrations.append("ALTER TABLE usuarios ADD COLUMN objetivo VARCHAR(80) DEFAULT 'organizar'")
        for migration in user_migrations:
            db.session.execute(text(migration))
        if user_migrations:
            Usuario.query.filter(Usuario.renda_mensal == None).update({"renda_mensal": 0})  # noqa: E711
            Usuario.query.filter((Usuario.objetivo == None) | (Usuario.objetivo == "")).update({"objetivo": "organizar"})  # noqa: E711
            db.session.commit()

    if "metas" not in table_names:
        return
    columns = {column["name"] for column in inspector.get_columns("metas")}
    migrations = []
    if "tipo_meta" not in columns:
        migrations.append("ALTER TABLE metas ADD COLUMN tipo_meta VARCHAR(30) DEFAULT 'economia'")
    if "valor_planejado_mensal" not in columns:
        migrations.append("ALTER TABLE metas ADD COLUMN valor_planejado_mensal FLOAT DEFAULT 0")
    for migration in migrations:
        db.session.execute(text(migration))
    if migrations:
        Meta.query.filter((Meta.tipo_meta == None) | (Meta.tipo_meta == "")).update({"tipo_meta": "economia"})  # noqa: E711
        Meta.query.filter(Meta.valor_planejado_mensal == None).update({"valor_planejado_mensal": 0})  # noqa: E711
        db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
