from flask import Blueprint, jsonify, request

from services.auth_service import jwt_required
from services.report_service import (
    gastos_por_categoria,
    metas_progresso,
    projecao_gastos,
    reserva_emergencia,
    resumo_anual,
    resumo_mensal,
    totais,
)

reports_bp = Blueprint("reports", __name__)


def filtros():
    return {
        "mes": request.args.get("mes"),
        "ano": request.args.get("ano"),
        "categoria": request.args.get("categoria"),
    }


@reports_bp.get("/dashboard")
@jwt_required
def dashboard(usuario):
    params = filtros()
    data = totais(usuario.id, **params)
    data["gastos_por_categoria"] = gastos_por_categoria(usuario.id, params["mes"], params["ano"])
    data["resumo_mensal"] = resumo_mensal(usuario.id, params["ano"])
    data["metas"] = metas_progresso(usuario.id)
    data["projecao_gastos"] = projecao_gastos(usuario.id)
    data["reserva_emergencia"] = reserva_emergencia(usuario.id)
    return jsonify(data)


@reports_bp.get("/saldo-atual")
@jwt_required
def saldo_atual(usuario):
    total = totais(usuario.id, **filtros())
    return jsonify({"saldo_atual": total["saldo_previsto"]})


@reports_bp.get("/resumo-mensal")
@jwt_required
def mensal(usuario):
    return jsonify(resumo_mensal(usuario.id, request.args.get("ano")))


@reports_bp.get("/resumo-anual")
@jwt_required
def anual(usuario):
    return jsonify(resumo_anual(usuario.id))


@reports_bp.get("/gastos-por-categoria")
@jwt_required
def categorias(usuario):
    return jsonify(gastos_por_categoria(usuario.id, request.args.get("mes"), request.args.get("ano")))


@reports_bp.get("/percentual-economia")
@jwt_required
def economia(usuario):
    total = totais(usuario.id, **filtros())
    return jsonify({"percentual_economia": total["percentual_economia"], "alerta_limite": total["alerta_limite"]})


@reports_bp.get("/projecao-gastos")
@jwt_required
def gastos_futuros(usuario):
    return jsonify(projecao_gastos(usuario.id, int(request.args.get("meses", 6))))


@reports_bp.get("/reserva-emergencia")
@jwt_required
def emergencia(usuario):
    return jsonify(reserva_emergencia(usuario.id))
