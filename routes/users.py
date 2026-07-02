from flask import Blueprint, jsonify, request

from database import db
from models import Usuario
from services.auth_service import jwt_required

users_bp = Blueprint("users", __name__)


@users_bp.get("/usuarios")
@jwt_required
def listar_usuarios(usuario):
    return jsonify([item.to_dict() for item in Usuario.query.order_by(Usuario.nome).all()])


@users_bp.get("/usuario/<int:id>")
@jwt_required
def obter_usuario(usuario, id):
    item = Usuario.query.get_or_404(id)
    return jsonify(item.to_dict())


@users_bp.put("/usuario/<int:id>")
@jwt_required
def atualizar_usuario(usuario, id):
    item = Usuario.query.get_or_404(id)
    payload = request.get_json() or {}
    for field in ("nome", "email", "objetivo"):
        if field in payload:
            setattr(item, field, payload[field])
    if "renda_mensal" in payload:
        item.renda_mensal = float(payload.get("renda_mensal") or 0)
    if payload.get("senha"):
        item.set_senha(payload["senha"])
    db.session.commit()
    return jsonify(item.to_dict())


@users_bp.delete("/usuario/<int:id>")
@jwt_required
def excluir_usuario(usuario, id):
    item = Usuario.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"mensagem": "Usuario removido"})
