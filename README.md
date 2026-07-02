# FinControl API

API REST em Flask para gestao financeira pessoal com SQLite, SQLAlchemy, JWT e Swagger/OpenAPI.

## Recursos

- Autenticacao com JWT: `/register`, `/login`, `/logout`
- CRUD de usuarios, receitas, despesas fixas, despesas variaveis, cartoes, faturas, reservas e metas
- Dividas parceladas com geracao automatica de parcelas futuras
- Metas financeiras com valor restante, percentual e previsao de conclusao
- Metas de investimento com aportes variaveis e previsao pela media mensal
- Dashboard com saldo previsto, economia, alertas e indicadores
- Relatorios mensal, anual, categorias, projecao de gastos e reserva de emergencia
- SQLite criado automaticamente em `fincontrol.db`
- Schema SQL de referencia em `schema.sql`
- Tratamento de erros em JSON para validacao, registros nao encontrados e restricoes do banco

## Novas regras financeiras

### Dividas parceladas

`POST /dividas-parceladas` recebe `descricao`, `valor_total`, `total_parcelas` e `data_inicial`. A API cria automaticamente as parcelas mensais, ajustando mes e ano quando passar de dezembro.

Rotas:

- `POST /dividas-parceladas`
- `GET /dividas-parceladas`
- `GET /dividas-parceladas/parcelas`
- `PUT /dividas-parceladas/<id>`
- `PUT /dividas-parceladas/parcela/<id>`
- `DELETE /dividas-parceladas/parcela/<id>`
- `DELETE /dividas-parceladas/<id>`

### Metas e investimentos

Metas comuns usam `valor_planejado_mensal` para estimar quantos meses faltam. Metas de investimento usam aportes em `/metas/<id>/aportes` e recalculam a previsao com base na media dos aportes registrados.

Rotas:

- `POST /metas`
- `GET /metas`
- `POST /metas/<id>/aportes`
- `GET /metas/<id>/aportes`
- `DELETE /metas/<id>/aportes/<aporte_id>`

## Dependencias

- Flask
- Flask-Cors
- Flask-SQLAlchemy
- flask-swagger-ui
- PyJWT
- Werkzeug

## Como executar

```bash
cd fincontrol-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

API: `http://127.0.0.1:5000`

Swagger: `http://127.0.0.1:5000/docs`

## Validacao e carga local

```bash
source .venv/bin/activate
python tests/smoke_test.py
python seed.py
```

Usuario inicial:

- Email: `admin@fincontrol.local`
- Senha: `123456`

## Checklist rapido

```bash
python -m py_compile app.py config.py database.py models.py routes/*.py services/*.py
python tests/smoke_test.py
curl http://127.0.0.1:5000/
```

## Autenticacao

1. Cadastre um usuario em `POST /register`.
2. Use o token retornado no header:

```http
Authorization: Bearer SEU_TOKEN
```

## Padrao de erros

As rotas retornam erros em JSON:

```json
{
  "erro": "Mensagem do erro",
  "status": 400
}
```

## Exemplo rapido

```bash
curl -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"nome":"Ana","email":"ana@fincontrol.com","senha":"123456"}'
```

## Estrutura

```text
fincontrol-api/
├── app.py
├── config.py
├── database.py
├── models.py
├── routes/
├── services/
├── swagger/
├── requirements.txt
└── README.md
```

## Variaveis de ambiente

- `SECRET_KEY`
- `JWT_SECRET`
- `DATABASE_URL`
