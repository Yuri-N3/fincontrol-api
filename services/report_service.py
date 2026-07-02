from collections import defaultdict
from datetime import date

from sqlalchemy import extract

from models import Receita, DespesaFixa, DespesaVariavel, Cartao, Fatura, Reserva, Meta, ParcelaDivida


def _filters(query, model, date_field, usuario_id, mes=None, ano=None, categoria=None):
    query = query.filter(model.usuario_id == usuario_id)
    column = getattr(model, date_field)
    if mes:
        query = query.filter(extract("month", column) == int(mes))
    if ano:
        query = query.filter(extract("year", column) == int(ano))
    if categoria and hasattr(model, "categoria"):
        query = query.filter(model.categoria == categoria)
    return query


def receitas(usuario_id, mes=None, ano=None, categoria=None):
    return _filters(Receita.query, Receita, "data_recebimento", usuario_id, mes, ano, categoria).all()


def despesas_fixas(usuario_id, mes=None, ano=None, categoria=None):
    return _filters(DespesaFixa.query, DespesaFixa, "vencimento", usuario_id, mes, ano, categoria).all()


def despesas_variaveis(usuario_id, mes=None, ano=None, categoria=None):
    return _filters(DespesaVariavel.query, DespesaVariavel, "data", usuario_id, mes, ano, categoria).all()


def parcelas_divida(usuario_id, mes=None, ano=None):
    query = ParcelaDivida.query.filter_by(usuario_id=usuario_id)
    if mes:
        query = query.filter(extract("month", ParcelaDivida.vencimento) == int(mes))
    if ano:
        query = query.filter(extract("year", ParcelaDivida.vencimento) == int(ano))
    return query.all()


def totais(usuario_id, mes=None, ano=None, categoria=None):
    rec = receitas(usuario_id, mes, ano, categoria)
    fixas = despesas_fixas(usuario_id, mes, ano, categoria)
    variaveis = despesas_variaveis(usuario_id, mes, ano, categoria)
    parcelas = parcelas_divida(usuario_id, mes, ano)
    cartoes = Cartao.query.filter_by(usuario_id=usuario_id).all()
    cartao_ids = [cartao.id for cartao in cartoes]
    faturas = Fatura.query.filter(Fatura.cartao_id.in_(cartao_ids)).all() if cartao_ids else []

    receita_prevista = sum(item.valor for item in rec)
    despesa_prevista = sum(item.valor_previsto for item in fixas + variaveis)
    total_pago = sum(item.valor_pago for item in fixas + variaveis)
    total_pendente = max(despesa_prevista - total_pago, 0)
    total_cartoes = sum(item.valor for item in faturas)
    total_dividas = sum(item.valor for item in parcelas)
    total_dividas_pagas = sum(item.valor for item in parcelas if item.status == "pago")
    total_dividas_pendentes = sum(item.valor for item in parcelas if item.status != "pago")
    despesas_total = despesa_prevista + total_cartoes + total_dividas
    saldo_previsto = receita_prevista - despesas_total
    percentual_economia = ((receita_prevista - despesas_total) / receita_prevista * 100) if receita_prevista else 0

    return {
        "receita_prevista": round(receita_prevista, 2),
        "despesa_prevista": round(despesa_prevista, 2),
        "saldo_previsto": round(saldo_previsto, 2),
        "total_pago": round(total_pago, 2),
        "total_pendente": round(total_pendente, 2),
        "total_cartoes": round(total_cartoes, 2),
        "total_dividas": round(total_dividas, 2),
        "total_dividas_pagas": round(total_dividas_pagas, 2),
        "total_dividas_pendentes": round(total_dividas_pendentes, 2),
        "economia_mes": round(max(saldo_previsto, 0), 2),
        "percentual_economia": round(percentual_economia, 2),
        "alerta_limite": despesas_total > receita_prevista * 0.8 if receita_prevista else False,
    }


def gastos_por_categoria(usuario_id, mes=None, ano=None):
    grupos = defaultdict(float)
    for item in despesas_fixas(usuario_id, mes, ano) + despesas_variaveis(usuario_id, mes, ano):
        grupos[item.categoria] += item.valor_pago or item.valor_previsto or 0
    dividas = sum(item.valor for item in parcelas_divida(usuario_id, mes, ano))
    if dividas:
        grupos["Dividas parceladas"] += dividas
    return [{"categoria": categoria, "valor": round(valor, 2)} for categoria, valor in grupos.items()]


def resumo_mensal(usuario_id, ano=None):
    ano = int(ano or date.today().year)
    meses = []
    for mes in range(1, 13):
        total = totais(usuario_id, mes, ano)
        meses.append({"mes": mes, **total})
    return meses


def resumo_anual(usuario_id):
    anos = set()
    for item in Receita.query.filter_by(usuario_id=usuario_id).all():
        anos.add(item.data_recebimento.year)
    for item in DespesaFixa.query.filter_by(usuario_id=usuario_id).all():
        anos.add(item.vencimento.year)
    for item in DespesaVariavel.query.filter_by(usuario_id=usuario_id).all():
        anos.add(item.data.year)
    return [{"ano": ano, **totais(usuario_id, ano=ano)} for ano in sorted(anos or {date.today().year})]


def projecao_gastos(usuario_id, meses_futuros=6):
    historico = resumo_mensal(usuario_id)
    gastos = [m["despesa_prevista"] + m["total_cartoes"] for m in historico if m["despesa_prevista"] or m["total_cartoes"]]
    media = sum(gastos) / len(gastos) if gastos else 0
    return [{"mes": i, "gasto_previsto": round(media, 2)} for i in range(1, meses_futuros + 1)]


def reserva_emergencia(usuario_id):
    mensal = resumo_mensal(usuario_id)
    despesas = [m["despesa_prevista"] + m["total_cartoes"] for m in mensal if m["despesa_prevista"] or m["total_cartoes"]]
    media = sum(despesas) / len(despesas) if despesas else 0
    ideal = media * 6
    reservas = Reserva.query.filter_by(usuario_id=usuario_id).all()
    atual = sum(item.valor for item in reservas)
    return {
        "media_despesas_mensais": round(media, 2),
        "reserva_ideal": round(ideal, 2),
        "valor_atual": round(atual, 2),
        "valor_faltante": round(max(ideal - atual, 0), 2),
        "percentual": round((atual / ideal * 100), 2) if ideal else 0,
    }


def metas_progresso(usuario_id):
    return [meta.to_dict() for meta in Meta.query.filter_by(usuario_id=usuario_id).all()]
