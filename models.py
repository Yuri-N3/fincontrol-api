from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

from database import db


class SerializerMixin:
    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            data[column.name] = value
        return data


class Usuario(db.Model, SerializerMixin):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    renda_mensal = db.Column(db.Float, default=0)
    objetivo = db.Column(db.String(80), default="organizar")
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    receitas = db.relationship("Receita", backref="usuario", cascade="all, delete-orphan")
    despesas_fixas = db.relationship("DespesaFixa", backref="usuario", cascade="all, delete-orphan")
    despesas_variaveis = db.relationship("DespesaVariavel", backref="usuario", cascade="all, delete-orphan")
    cartoes = db.relationship("Cartao", backref="usuario", cascade="all, delete-orphan")
    reservas = db.relationship("Reserva", backref="usuario", cascade="all, delete-orphan")
    metas = db.relationship("Meta", backref="usuario", cascade="all, delete-orphan")
    dividas = db.relationship("DividaParcelada", backref="usuario", cascade="all, delete-orphan")

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        data = super().to_dict()
        data.pop("senha_hash", None)
        return data


class Receita(db.Model, SerializerMixin):
    __tablename__ = "receitas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    descricao = db.Column(db.String(160), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(80), nullable=False)
    data_recebimento = db.Column(db.Date, nullable=False)


class DespesaFixa(db.Model, SerializerMixin):
    __tablename__ = "despesas_fixas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    descricao = db.Column(db.String(160), nullable=False)
    categoria = db.Column(db.String(80), nullable=False)
    valor_previsto = db.Column(db.Float, nullable=False)
    valor_pago = db.Column(db.Float, default=0)
    vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), default="pendente")


class DespesaVariavel(db.Model, SerializerMixin):
    __tablename__ = "despesas_variaveis"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    descricao = db.Column(db.String(160), nullable=False)
    categoria = db.Column(db.String(80), nullable=False)
    valor_previsto = db.Column(db.Float, nullable=False)
    valor_pago = db.Column(db.Float, default=0)
    data = db.Column(db.Date, nullable=False)


class Cartao(db.Model, SerializerMixin):
    __tablename__ = "cartoes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    nome_cartao = db.Column(db.String(120), nullable=False)
    limite = db.Column(db.Float, nullable=False)
    fechamento = db.Column(db.Integer, nullable=False)
    vencimento = db.Column(db.Integer, nullable=False)

    faturas = db.relationship("Fatura", backref="cartao", cascade="all, delete-orphan")


class Fatura(db.Model, SerializerMixin):
    __tablename__ = "faturas"

    id = db.Column(db.Integer, primary_key=True)
    cartao_id = db.Column(db.Integer, db.ForeignKey("cartoes.id"), nullable=False)
    descricao = db.Column(db.String(160), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="aberta")


class Reserva(db.Model, SerializerMixin):
    __tablename__ = "reservas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tipo_reserva = db.Column(db.String(80), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_aporte = db.Column(db.Date, nullable=False)


class Meta(db.Model, SerializerMixin):
    __tablename__ = "metas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    titulo = db.Column(db.String(140), nullable=False)
    valor_meta = db.Column(db.Float, nullable=False)
    valor_atual = db.Column(db.Float, default=0)
    tipo_meta = db.Column(db.String(30), default="economia")
    valor_planejado_mensal = db.Column(db.Float, default=0)
    prazo = db.Column(db.Date, nullable=False)

    aportes = db.relationship("AporteInvestimento", backref="meta", cascade="all, delete-orphan")

    def to_dict(self):
        data = super().to_dict()
        total_aportes = sum(aporte.valor for aporte in self.aportes)
        valor_acumulado = total_aportes if self.tipo_meta == "investimento" else (self.valor_atual or 0)
        valor_restante = max((self.valor_meta or 0) - valor_acumulado, 0)
        media_aportes = total_aportes / len(self.aportes) if self.aportes else 0
        base_mensal = media_aportes if self.tipo_meta == "investimento" else (self.valor_planejado_mensal or 0)
        meses_estimados = int(-(-valor_restante // base_mensal)) if base_mensal else None
        data["valor_acumulado"] = round(valor_acumulado, 2)
        data["valor_restante"] = round(valor_restante, 2)
        data["percentual"] = round((valor_acumulado / self.valor_meta * 100), 2) if self.valor_meta else 0
        data["media_aportes"] = round(media_aportes, 2)
        data["meses_estimados"] = meses_estimados
        data["previsao_conclusao"] = add_months(date.today(), meses_estimados).isoformat() if meses_estimados else None
        return data


class DividaParcelada(db.Model, SerializerMixin):
    __tablename__ = "dividas_parceladas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    descricao = db.Column(db.String(160), nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    total_parcelas = db.Column(db.Integer, nullable=False)
    data_inicial = db.Column(db.Date, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    parcelas = db.relationship("ParcelaDivida", backref="divida", cascade="all, delete-orphan")

    def to_dict(self):
        data = super().to_dict()
        parcelas = sorted(self.parcelas, key=lambda item: item.numero_parcela)
        data["parcelas"] = [parcela.to_dict() for parcela in parcelas]
        data["total_pago"] = round(sum(parcela.valor for parcela in parcelas if parcela.status == "pago"), 2)
        data["total_pendente"] = round(sum(parcela.valor for parcela in parcelas if parcela.status != "pago"), 2)
        return data


class ParcelaDivida(db.Model, SerializerMixin):
    __tablename__ = "parcelas_divida"

    id = db.Column(db.Integer, primary_key=True)
    divida_id = db.Column(db.Integer, db.ForeignKey("dividas_parceladas.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    descricao = db.Column(db.String(180), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    numero_parcela = db.Column(db.Integer, nullable=False)
    total_parcelas = db.Column(db.Integer, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), default="pendente")

    def to_dict(self):
        data = super().to_dict()
        data["rotulo_parcela"] = f"{self.numero_parcela}/{self.total_parcelas}"
        return data


class AporteInvestimento(db.Model, SerializerMixin):
    __tablename__ = "aportes_investimento"

    id = db.Column(db.Integer, primary_key=True)
    meta_id = db.Column(db.Integer, db.ForeignKey("metas.id"), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_aporte = db.Column(db.Date, nullable=False)


def add_months(start_date, months):
    if not months:
        return start_date
    month = start_date.month - 1 + int(months)
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, days_in_month(year, month))
    return date(year, month, day)


def days_in_month(year, month):
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return (next_month - date(year, month, 1)).days
