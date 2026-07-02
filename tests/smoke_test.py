import os
import sys
import tempfile
from pathlib import Path

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.NamedTemporaryFile(delete=False).name}"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from database import db  # noqa: E402


def assert_ok(response, expected_status=200):
    assert response.status_code == expected_status, response.get_data(as_text=True)
    return response.get_json()


def main():
    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        db.drop_all()
        db.create_all()

    client = app.test_client()

    auth = assert_ok(
        client.post(
            "/register",
            json={"nome": "Ana Silva", "email": "ana@fincontrol.com", "senha": "123456"},
        ),
        201,
    )
    token = auth["token"]
    headers = {"Authorization": f"Bearer {token}"}

    receita = assert_ok(
        client.post(
            "/receitas",
            headers=headers,
            json={
                "descricao": "Salario",
                "valor": 7500,
                "categoria": "Trabalho",
                "data_recebimento": "2026-06-05",
            },
        ),
        201,
    )
    assert_ok(client.get(f"/receitas/{receita['id']}", headers=headers))

    assert_ok(
        client.post(
            "/despesas-fixas",
            headers=headers,
            json={
                "descricao": "Aluguel",
                "categoria": "Moradia",
                "valor_previsto": 2200,
                "valor_pago": 2200,
                "vencimento": "2026-06-10",
                "status": "pago",
            },
        ),
        201,
    )
    assert_ok(
        client.post(
            "/despesas-variaveis",
            headers=headers,
            json={
                "descricao": "Mercado",
                "categoria": "Alimentacao",
                "valor_previsto": 900,
                "valor_pago": 860,
                "data": "2026-06-14",
            },
        ),
        201,
    )
    cartao = assert_ok(
        client.post(
            "/cartoes",
            headers=headers,
            json={"nome_cartao": "Platinum", "limite": 8000, "fechamento": 20, "vencimento": 28},
        ),
        201,
    )
    fatura = assert_ok(
        client.post(
            "/cartoes/fatura",
            headers=headers,
            json={"cartao_id": cartao["id"], "descricao": "Farmacia", "valor": 120, "status": "aberta"},
        ),
        201,
    )
    assert_ok(client.put(f"/cartoes/fatura/{fatura['id']}", headers=headers, json={"status": "paga"}))

    assert_ok(
        client.post(
            "/reservas",
            headers=headers,
            json={"tipo_reserva": "Emergencia", "valor": 1500, "data_aporte": "2026-06-15"},
        ),
        201,
    )
    assert_ok(
        client.post(
            "/metas",
            headers=headers,
            json={
                "titulo": "Viagem",
                "valor_meta": 40000,
                "valor_atual": 6000,
                "valor_planejado_mensal": 300,
                "tipo_meta": "economia",
                "prazo": "2027-12-31",
            },
        ),
        201,
    )
    investimento = assert_ok(
        client.post(
            "/metas",
            headers=headers,
            json={
                "titulo": "Investimentos",
                "valor_meta": 100000,
                "valor_atual": 0,
                "tipo_meta": "investimento",
                "prazo": "2030-12-31",
            },
        ),
        201,
    )
    assert_ok(
        client.post(
            f"/metas/{investimento['id']}/aportes",
            headers=headers,
            json={"valor": 300, "data_aporte": "2026-07-05"},
        ),
        201,
    )
    assert_ok(
        client.post(
            f"/metas/{investimento['id']}/aportes",
            headers=headers,
            json={"valor": 500, "data_aporte": "2026-08-05"},
        ),
        201,
    )
    assert_ok(client.get(f"/metas/{investimento['id']}/aportes", headers=headers))

    divida = assert_ok(
        client.post(
            "/dividas-parceladas",
            headers=headers,
            json={
                "descricao": "Notebook",
                "valor_total": 4800,
                "total_parcelas": 12,
                "data_inicial": "2026-07-10",
            },
        ),
        201,
    )
    assert len(divida["parcelas"]) == 12
    assert divida["parcelas"][5]["vencimento"] == "2026-12-10"
    assert divida["parcelas"][6]["vencimento"] == "2027-01-10"
    divida_editada = assert_ok(
        client.put(
            f"/dividas-parceladas/{divida['id']}",
            headers=headers,
            json={
                "descricao": "Notebook Pro",
                "valor_total": 6000,
                "total_parcelas": 10,
                "data_inicial": "2026-08-10",
                "regenerar_parcelas": True,
            },
        )
    )
    assert len(divida_editada["parcelas"]) == 10
    assert divida_editada["parcelas"][0]["descricao"] == "Notebook Pro (1/10)"
    parcela_id = divida_editada["parcelas"][0]["id"]
    assert_ok(client.put(f"/dividas-parceladas/parcela/{parcela_id}", headers=headers, json={"status": "pago"}))
    assert_ok(client.get("/dividas-parceladas/parcelas", headers=headers))
    assert_ok(client.get("/dividas-parceladas/parcelas?mes=8&ano=2026&status=pendente", headers=headers))

    for path in (
        "/dashboard",
        "/saldo-atual",
        "/resumo-mensal",
        "/resumo-anual",
        "/gastos-por-categoria",
        "/percentual-economia",
        "/projecao-gastos",
        "/reserva-emergencia",
        "/usuarios",
        "/dividas-parceladas",
    ):
        assert_ok(client.get(path, headers=headers))

    assert_ok(client.post("/logout", headers=headers))
    print("Smoke test OK: autenticacao, CRUDs, faturas e relatorios funcionando.")


if __name__ == "__main__":
    main()
