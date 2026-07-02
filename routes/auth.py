from flask import Blueprint, jsonify, request

from database import db
from models import Usuario
from services.auth_service import gerar_token, jwt_required
from services.crud_service import ValidationError

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    payload = request.get_json() or {}
    if not all(payload.get(field) for field in ("nome", "email", "senha")):
        raise ValidationError("Nome, email e senha sao obrigatorios")
    email = payload["email"].strip().lower()
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"erro": "Email ja cadastrado"}), 409
    try:
        renda_mensal = float(payload.get("renda_mensal") or 0)
    except (TypeError, ValueError):
        raise ValidationError("Renda mensal precisa ser um numero")
    usuario = Usuario(
        nome=payload["nome"].strip(),
        email=email,
        renda_mensal=renda_mensal,
        objetivo=payload.get("objetivo") or "organizar",
    )
    usuario.set_senha(payload["senha"])
    db.session.add(usuario)
    db.session.commit()
    return jsonify({"usuario": usuario.to_dict(), "token": gerar_token(usuario)}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json() or {}
    if not payload.get("email") or not payload.get("senha"):
        raise ValidationError("Email e senha sao obrigatorios")
    usuario = Usuario.query.filter_by(email=payload.get("email")).first()
    if not usuario or not usuario.verificar_senha(payload.get("senha", "")):
        return jsonify({"erro": "Credenciais invalidas"}), 401
    return jsonify({"usuario": usuario.to_dict(), "token": gerar_token(usuario)})


@auth_bp.post("/logout")
@jwt_required
def logout(usuario):
    return jsonify({"mensagem": "Logout realizado no cliente removendo o token", "usuario_id": usuario.id})
