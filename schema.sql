CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  senha_hash VARCHAR(255) NOT NULL,
  data_criacao DATETIME
);

CREATE INDEX IF NOT EXISTS ix_usuarios_email ON usuarios (email);

CREATE TABLE IF NOT EXISTS receitas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL,
  descricao VARCHAR(160) NOT NULL,
  valor FLOAT NOT NULL,
  categoria VARCHAR(80) NOT NULL,
  data_recebimento DATE NOT NULL,
  FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS despesas_fixas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL,
  descricao VARCHAR(160) NOT NULL,
  categoria VARCHAR(80) NOT NULL,
  valor_previsto FLOAT NOT NULL,
  valor_pago FLOAT,
  vencimento DATE NOT NULL,
  status VARCHAR(30),
  FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS despesas_variaveis (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL,
  descricao VARCHAR(160) NOT NULL,
  categoria VARCHAR(80) NOT NULL,
  valor_previsto FLOAT NOT NULL,
  valor_pago FLOAT,
  data DATE NOT NULL,
  FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS cartoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL,
  nome_cartao VARCHAR(120) NOT NULL,
  limite FLOAT NOT NULL,
  fechamento INTEGER NOT NULL,
  vencimento INTEGER NOT NULL,
  FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS faturas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cartao_id INTEGER NOT NULL,
  descricao VARCHAR(160) NOT NULL,
  valor FLOAT NOT NULL,
  status VARCHAR(30),
  FOREIGN KEY(cartao_id) REFERENCES cartoes (id)
);

CREATE TABLE IF NOT EXISTS reservas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL,
  tipo_reserva VARCHAR(80) NOT NULL,
  valor FLOAT NOT NULL,
  data_aporte DATE NOT NULL,
  FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS metas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL,
  titulo VARCHAR(140) NOT NULL,
  valor_meta FLOAT NOT NULL,
  valor_atual FLOAT,
  tipo_meta VARCHAR(30),
  valor_planejado_mensal FLOAT,
  prazo DATE NOT NULL,
  FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS dividas_parceladas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL,
  descricao VARCHAR(160) NOT NULL,
  valor_total FLOAT NOT NULL,
  total_parcelas INTEGER NOT NULL,
  data_inicial DATE NOT NULL,
  data_criacao DATETIME,
  FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS parcelas_divida (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  divida_id INTEGER NOT NULL,
  usuario_id INTEGER NOT NULL,
  descricao VARCHAR(180) NOT NULL,
  valor FLOAT NOT NULL,
  numero_parcela INTEGER NOT NULL,
  total_parcelas INTEGER NOT NULL,
  vencimento DATE NOT NULL,
  status VARCHAR(30),
  FOREIGN KEY(divida_id) REFERENCES dividas_parceladas (id),
  FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS aportes_investimento (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  meta_id INTEGER NOT NULL,
  valor FLOAT NOT NULL,
  data_aporte DATE NOT NULL,
  FOREIGN KEY(meta_id) REFERENCES metas (id)
);
