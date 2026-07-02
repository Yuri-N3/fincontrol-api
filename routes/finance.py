from flask import Blueprint, jsonify, request
from sqlalchemy import extract

from models import (
    Receita,
    DespesaFixa,
    DespesaVariavel,
    Cartao,
    Fatura,
    Reserva,
    Meta,
    DividaParcelada,
    ParcelaDivida,
    AporteInvestimento,
    add_months,
)
from services.auth_service import jwt_required
from services.crud_service import apply_payload, save, delete, validate_payload, parse_date, ValidationError

finance_bp = Blueprint("finance", __name__)


CONFIG = {
    "receitas": {
        "model": Receita,
        "fields": ("descricao", "valor", "categoria", "data_recebimento"),
        "required": ("descricao", "valor", "categoria", "data_recebimento"),
        "numeric": ("valor",),
        "dates": {"data_recebimento"},
    },
    "despesas-fixas": {
        "model": DespesaFixa,
        "fields": ("descricao", "categoria", "valor_previsto", "valor_pago", "vencimento", "status"),
        "required": ("descricao", "categoria", "valor_previsto", "vencimento"),
        "numeric": ("valor_previsto", "valor_pago"),
        "dates": {"vencimento"},
    },
    "despesas-variaveis": {
        "model": DespesaVariavel,
        "fields": ("descricao", "categoria", "valor_previsto", "valor_pago", "data"),
        "required": ("descricao", "categoria", "valor_previsto", "data"),
        "numeric": ("valor_previsto", "valor_pago"),
        "dates": {"data"},
    },
    "cartoes": {
        "model": Cartao,
        "fields": ("nome_cartao", "limite", "fechamento", "vencimento"),
        "required": ("nome_cartao", "limite", "fechamento", "vencimento"),
        "numeric": ("limite", "fechamento", "vencimento"),
        "dates": set(),
    },
    "reservas": {
        "model": Reserva,
        "fields": ("tipo_reserva", "valor", "data_aporte"),
        "required": ("tipo_reserva", "valor", "data_aporte"),
        "numeric": ("valor",),
        "dates": {"data_aporte"},
    },
    "metas": {
        "model": Meta,
        "fields": ("titulo", "valor_meta", "valor_atual", "tipo_meta", "valor_planejado_mensal", "prazo"),
        "required": ("titulo", "valor_meta", "prazo"),
        "numeric": ("valor_meta", "valor_atual", "valor_planejado_mensal"),
        "dates": {"prazo"},
    },
}


def scoped_query(model, usuario_id):
    return model.query.filter_by(usuario_id=usuario_id)


def create_item(kind):
    config = CONFIG[kind]
    payload = request.get_json() or {}
    validate_payload(payload, config["required"], config["numeric"])
    item = config["model"](usuario_id=request.current_user.id)
    apply_payload(item, payload, config["dates"], config["fields"])
    save(item)
    return jsonify(item.to_dict()), 201


def list_items(kind):
    config = CONFIG[kind]
    items = scoped_query(config["model"], request.current_user.id).all()
    return jsonify([item.to_dict() for item in items])


def get_item(kind, id):
    config = CONFIG[kind]
    item = scoped_query(config["model"], request.current_user.id).filter_by(id=id).first_or_404()
    return jsonify(item.to_dict())


def update_item(kind, id):
    config = CONFIG[kind]
    item = scoped_query(config["model"], request.current_user.id).filter_by(id=id).first_or_404()
    payload = request.get_json() or {}
    validate_payload(payload, numeric_fields=config["numeric"])
    apply_payload(item, payload, config["dates"], config["fields"])
    save(item)
    return jsonify(item.to_dict())


def delete_item(kind, id):
    config = CONFIG[kind]
    item = scoped_query(config["model"], request.current_user.id).filter_by(id=id).first_or_404()
    delete(item)
    return jsonify({"mensagem": "Registro removido"})


def with_user(fn):
    @jwt_required
    def wrapper(usuario, *args, **kwargs):
        request.current_user = usuario
        return fn(*args, **kwargs)
    wrapper.__name__ = f"{fn.__name__}_{id(fn)}"
    return wrapper


def build_parcelas(usuario_id, descricao, valor_total, total_parcelas, data_inicial, status="pendente"):
    valor_parcela = round(valor_total / total_parcelas, 2)
    parcelas = []
    for numero in range(1, total_parcelas + 1):
        valor = valor_parcela
        if numero == total_parcelas:
            valor = round(valor_total - (valor_parcela * (total_parcelas - 1)), 2)
        parcelas.append(
            ParcelaDivida(
                usuario_id=usuario_id,
                descricao=f"{descricao} ({numero}/{total_parcelas})",
                valor=valor,
                numero_parcela=numero,
                total_parcelas=total_parcelas,
                vencimento=add_months(data_inicial, numero - 1),
                status=status,
            )
        )
    return parcelas


for endpoint in ("receitas", "despesas-fixas", "despesas-variaveis", "cartoes", "reservas", "metas"):
    finance_bp.add_url_rule(f"/{endpoint}", f"create_{endpoint}", with_user(lambda endpoint=endpoint: create_item(endpoint)), methods=["POST"])
    finance_bp.add_url_rule(f"/{endpoint}", f"list_{endpoint}", with_user(lambda endpoint=endpoint: list_items(endpoint)), methods=["GET"])

finance_bp.add_url_rule("/receitas/<int:id>", "get_receitas", with_user(lambda id: get_item("receitas", id)), methods=["GET"])
finance_bp.add_url_rule("/receitas/<int:id>", "update_receitas", with_user(lambda id: update_item("receitas", id)), methods=["PUT"])
finance_bp.add_url_rule("/receitas/<int:id>", "delete_receitas", with_user(lambda id: delete_item("receitas", id)), methods=["DELETE"])

for endpoint in ("despesas-fixas", "despesas-variaveis", "cartoes", "reservas", "metas"):
    finance_bp.add_url_rule(f"/{endpoint}/<int:id>", f"update_{endpoint}", with_user(lambda id, endpoint=endpoint: update_item(endpoint, id)), methods=["PUT"])
    finance_bp.add_url_rule(f"/{endpoint}/<int:id>", f"delete_{endpoint}", with_user(lambda id, endpoint=endpoint: delete_item(endpoint, id)), methods=["DELETE"])


@finance_bp.post("/cartoes/fatura")
@jwt_required
def criar_fatura(usuario):
    payload = request.get_json() or {}
    validate_payload(payload, ("cartao_id", "descricao", "valor"), ("cartao_id", "valor"))
    cartao = Cartao.query.filter_by(id=payload.get("cartao_id"), usuario_id=usuario.id).first_or_404()
    fatura = Fatura(cartao_id=cartao.id)
    apply_payload(fatura, payload, allowed_fields=("descricao", "valor", "status"))
    save(fatura)
    return jsonify(fatura.to_dict()), 201


@finance_bp.get("/cartoes/faturas")
@jwt_required
def listar_faturas(usuario):
    cartoes = Cartao.query.filter_by(usuario_id=usuario.id).all()
    ids = [cartao.id for cartao in cartoes]
    faturas = Fatura.query.filter(Fatura.cartao_id.in_(ids)).all() if ids else []
    return jsonify([fatura.to_dict() for fatura in faturas])


@finance_bp.put("/cartoes/fatura/<int:id>")
@jwt_required
def atualizar_fatura(usuario, id):
    ids = [cartao.id for cartao in Cartao.query.filter_by(usuario_id=usuario.id).all()]
    fatura = Fatura.query.filter(Fatura.id == id, Fatura.cartao_id.in_(ids)).first_or_404()
    payload = request.get_json() or {}
    validate_payload(payload, numeric_fields=("valor",))
    apply_payload(fatura, payload, allowed_fields=("descricao", "valor", "status"))
    save(fatura)
    return jsonify(fatura.to_dict())


@finance_bp.delete("/cartoes/fatura/<int:id>")
@jwt_required
def excluir_fatura(usuario, id):
    ids = [cartao.id for cartao in Cartao.query.filter_by(usuario_id=usuario.id).all()]
    fatura = Fatura.query.filter(Fatura.id == id, Fatura.cartao_id.in_(ids)).first_or_404()
    delete(fatura)
    return jsonify({"mensagem": "Fatura removida"})


@finance_bp.post("/dividas-parceladas")
@jwt_required
def criar_divida_parcelada(usuario):
    payload = request.get_json() or {}
    validate_payload(
        payload,
        ("descricao", "valor_total", "total_parcelas", "data_inicial"),
        ("valor_total", "total_parcelas"),
    )
    total_parcelas = int(payload["total_parcelas"])
    if total_parcelas <= 0:
        raise ValidationError("Total de parcelas deve ser maior que zero")
    valor_total = float(payload["valor_total"])
    data_inicial = parse_date(payload["data_inicial"])

    divida = DividaParcelada(
        usuario_id=usuario.id,
        descricao=payload["descricao"],
        valor_total=valor_total,
        total_parcelas=total_parcelas,
        data_inicial=data_inicial,
    )
    divida.parcelas = build_parcelas(usuario.id, payload["descricao"], valor_total, total_parcelas, data_inicial, payload.get("status", "pendente"))
    save(divida)
    return jsonify(divida.to_dict()), 201


@finance_bp.get("/dividas-parceladas")
@jwt_required
def listar_dividas_parceladas(usuario):
    dividas = DividaParcelada.query.filter_by(usuario_id=usuario.id).order_by(DividaParcelada.id.desc()).all()
    return jsonify([divida.to_dict() for divida in dividas])


@finance_bp.put("/dividas-parceladas/<int:id>")
@jwt_required
def atualizar_divida_parcelada(usuario, id):
    divida = DividaParcelada.query.filter_by(id=id, usuario_id=usuario.id).first_or_404()
    payload = request.get_json() or {}
    validate_payload(payload, numeric_fields=("valor_total", "total_parcelas"))

    descricao = payload.get("descricao", divida.descricao)
    valor_total = float(payload.get("valor_total", divida.valor_total))
    total_parcelas = int(payload.get("total_parcelas", divida.total_parcelas))
    data_inicial = parse_date(payload.get("data_inicial")) if payload.get("data_inicial") else divida.data_inicial
    if total_parcelas <= 0:
        raise ValidationError("Total de parcelas deve ser maior que zero")

    regenerate = bool(payload.get("regenerar_parcelas", True))
    divida.descricao = descricao
    divida.valor_total = valor_total
    divida.total_parcelas = total_parcelas
    divida.data_inicial = data_inicial

    if regenerate:
        divida.parcelas = build_parcelas(usuario.id, descricao, valor_total, total_parcelas, data_inicial, payload.get("status", "pendente"))
    else:
        for parcela in divida.parcelas:
            parcela.total_parcelas = total_parcelas
            parcela.descricao = f"{descricao} ({parcela.numero_parcela}/{parcela.total_parcelas})"

    save(divida)
    return jsonify(divida.to_dict())


@finance_bp.get("/dividas-parceladas/parcelas")
@jwt_required
def listar_parcelas_divida(usuario):
    query = ParcelaDivida.query.filter_by(usuario_id=usuario.id)
    status = request.args.get("status")
    mes = request.args.get("mes")
    ano = request.args.get("ano")
    if status:
        query = query.filter_by(status=status)
    if mes:
        query = query.filter(extract("month", ParcelaDivida.vencimento) == int(mes))
    if ano:
        query = query.filter(extract("year", ParcelaDivida.vencimento) == int(ano))
    parcelas = query.order_by(ParcelaDivida.vencimento.asc()).all()
    return jsonify([parcela.to_dict() for parcela in parcelas])


@finance_bp.put("/dividas-parceladas/parcela/<int:id>")
@jwt_required
def atualizar_parcela_divida(usuario, id):
    parcela = ParcelaDivida.query.filter_by(id=id, usuario_id=usuario.id).first_or_404()
    payload = request.get_json() or {}
    validate_payload(payload, numeric_fields=("valor",))
    apply_payload(parcela, payload, {"vencimento"}, ("descricao", "valor", "vencimento", "status"))
    save(parcela)
    return jsonify(parcela.to_dict())


@finance_bp.delete("/dividas-parceladas/parcela/<int:id>")
@jwt_required
def excluir_parcela_divida(usuario, id):
    parcela = ParcelaDivida.query.filter_by(id=id, usuario_id=usuario.id).first_or_404()
    delete(parcela)
    return jsonify({"mensagem": "Parcela removida"})


@finance_bp.delete("/dividas-parceladas/<int:id>")
@jwt_required
def excluir_divida_parcelada(usuario, id):
    divida = DividaParcelada.query.filter_by(id=id, usuario_id=usuario.id).first_or_404()
    delete(divida)
    return jsonify({"mensagem": "Divida parcelada removida"})


@finance_bp.post("/metas/<int:id>/aportes")
@jwt_required
def criar_aporte_investimento(usuario, id):
    meta = Meta.query.filter_by(id=id, usuario_id=usuario.id).first_or_404()
    payload = request.get_json() or {}
    validate_payload(payload, ("valor", "data_aporte"), ("valor",))
    aporte = AporteInvestimento(
        meta_id=meta.id,
        valor=payload["valor"],
        data_aporte=parse_date(payload["data_aporte"]),
    )
    save(aporte)
    return jsonify(meta.to_dict()), 201


@finance_bp.get("/metas/<int:id>/aportes")
@jwt_required
def listar_aportes_investimento(usuario, id):
    meta = Meta.query.filter_by(id=id, usuario_id=usuario.id).first_or_404()
    aportes = AporteInvestimento.query.filter_by(meta_id=meta.id).order_by(AporteInvestimento.data_aporte.asc()).all()
    return jsonify([aporte.to_dict() for aporte in aportes])


@finance_bp.delete("/metas/<int:id>/aportes/<int:aporte_id>")
@jwt_required
def excluir_aporte_investimento(usuario, id, aporte_id):
    meta = Meta.query.filter_by(id=id, usuario_id=usuario.id).first_or_404()
    aporte = AporteInvestimento.query.filter_by(id=aporte_id, meta_id=meta.id).first_or_404()
    delete(aporte)
    return jsonify(meta.to_dict())
