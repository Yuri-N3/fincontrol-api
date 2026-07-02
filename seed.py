from app import create_app
from database import db
from models import Usuario
from services.crud_service import parse_date
from models import Receita, DespesaFixa, DespesaVariavel, Cartao, Fatura, Reserva, Meta, DividaParcelada, ParcelaDivida, AporteInvestimento, add_months


def first_or_create_user():
    usuario = Usuario.query.filter_by(email="admin@fincontrol.local").first()
    if usuario:
        return usuario
    usuario = Usuario(nome="Administrador", email="admin@fincontrol.local")
    usuario.set_senha("123456")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def seed():
    app = create_app()
    with app.app_context():
        usuario = first_or_create_user()
        if Receita.query.filter_by(usuario_id=usuario.id).first():
            print("Base local ja possui dados.")
            return

        db.session.add_all(
            [
                Receita(usuario_id=usuario.id, descricao="Salario", valor=7800, categoria="Trabalho", data_recebimento=parse_date("2026-06-05")),
                Receita(usuario_id=usuario.id, descricao="Freelance", valor=1200, categoria="Extra", data_recebimento=parse_date("2026-06-18")),
                DespesaFixa(usuario_id=usuario.id, descricao="Aluguel", categoria="Moradia", valor_previsto=2300, valor_pago=2300, vencimento=parse_date("2026-06-10"), status="pago"),
                DespesaFixa(usuario_id=usuario.id, descricao="Internet", categoria="Servicos", valor_previsto=140, valor_pago=140, vencimento=parse_date("2026-06-12"), status="pago"),
                DespesaVariavel(usuario_id=usuario.id, descricao="Mercado", categoria="Alimentacao", valor_previsto=950, valor_pago=890, data=parse_date("2026-06-14")),
                DespesaVariavel(usuario_id=usuario.id, descricao="Transporte", categoria="Mobilidade", valor_previsto=450, valor_pago=420, data=parse_date("2026-06-20")),
                Reserva(usuario_id=usuario.id, tipo_reserva="Emergencia", valor=8500, data_aporte=parse_date("2026-06-15")),
                Meta(usuario_id=usuario.id, titulo="Viagem", valor_meta=40000, valor_atual=6000, valor_planejado_mensal=300, tipo_meta="economia", prazo=parse_date("2027-12-31")),
            ]
        )
        investimento = Meta(usuario_id=usuario.id, titulo="Carteira de investimentos", valor_meta=100000, valor_atual=0, tipo_meta="investimento", prazo=parse_date("2030-12-31"))
        db.session.add(investimento)
        db.session.flush()
        db.session.add_all(
            [
                AporteInvestimento(meta_id=investimento.id, valor=300, data_aporte=parse_date("2026-07-05")),
                AporteInvestimento(meta_id=investimento.id, valor=500, data_aporte=parse_date("2026-08-05")),
                AporteInvestimento(meta_id=investimento.id, valor=200, data_aporte=parse_date("2026-09-05")),
            ]
        )
        divida = DividaParcelada(usuario_id=usuario.id, descricao="Notebook", valor_total=4800, total_parcelas=12, data_inicial=parse_date("2026-07-10"))
        for numero in range(1, 13):
            divida.parcelas.append(
                ParcelaDivida(
                    usuario_id=usuario.id,
                    descricao=f"Notebook ({numero}/12)",
                    valor=400,
                    numero_parcela=numero,
                    total_parcelas=12,
                    vencimento=add_months(parse_date("2026-07-10"), numero - 1),
                    status="pendente",
                )
            )
        db.session.add(divida)
        cartao = Cartao(usuario_id=usuario.id, nome_cartao="Fin Platinum", limite=9000, fechamento=20, vencimento=28)
        db.session.add(cartao)
        db.session.flush()
        db.session.add_all(
            [
                Fatura(cartao_id=cartao.id, descricao="Farmacia", valor=180, status="aberta"),
                Fatura(cartao_id=cartao.id, descricao="Assinaturas", valor=96, status="aberta"),
            ]
        )
        db.session.commit()
        print("Dados locais criados: admin@fincontrol.local / 123456")


if __name__ == "__main__":
    seed()
