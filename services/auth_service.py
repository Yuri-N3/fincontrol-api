from datetime import datetime
from functools import wraps

import jwt
from flask import current_app, jsonify, request

from models import Usuario


def gerar_token(usuario):
    payload = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "exp": datetime.utcnow() + current_app.config["JWT_EXPIRATION"],
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def usuario_autenticado():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
        return Usuario.query.get(int(payload["sub"]))
    except jwt.PyJWTError:
        return None


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        usuario = usuario_autenticado()
        if not usuario:
            return jsonify({"erro": "Token ausente ou invalido"}), 401
        return fn(usuario, *args, **kwargs)

    return wrapper
