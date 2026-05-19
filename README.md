# registro-ponto-rpa

Automação RPA em Python que simula o acesso ao **Portal Ponto Ágil** (site externo de registro de ponto), faz **web scraping** das batidas e envia os dados para o `registro-ponto-backend`. O gestor visualiza as importações no **Flutter Web** (`registro-ponto-frontend` → aba **RPA**).

Este repositório faz parte do teste técnico **Sistema de Registro de Ponto** (Player Contabilidade), junto com:

| Repositório | Papel |
|-------------|--------|
| [registro-ponto-backend](https://github.com/Sistema-de-Registro-de-Ponto/registro-ponto-backend) | API REST, regras de negócio, MySQL |
| [registro-ponto-frontend](https://github.com/Sistema-de-Registro-de-Ponto/registro-ponto-frontend) | Flutter Web (colaborador + gestão) |
| **registro-ponto-rpa** (este) | Robô Python + portal mock |

### Requisitos

- **Python 3.11+**
- **Chromium** do Playwright (`playwright install chromium`)
- **Backend** em execução (`registro-ponto-backend` na porta `8080`) — obrigatório para importação completa; opcional para `--scrape-only`
- **MySQL** configurado conforme o backend

### Configuração do ambiente

```powershell
cd registro-ponto-rpa

# Ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
playwright install chromium

# Variáveis locais
copy .env.example .env          # Windows
# cp .env.example .env          # Linux/macOS
```

Edite o `.env` se necessário. A **`RPA_API_KEY`** deve ser **idêntica** à do backend (ver secção abaixo).

### Variáveis de ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `PORTAL_BASE_URL` | `http://localhost:5500` | URL do portal (mock local ou Ponto Ágil real) |
| `PORTAL_USERNAME` | `demo` | Usuário do portal |
| `PORTAL_PASSWORD` | `demo123` | Senha do portal |
| `API_BASE_URL` | `http://localhost:8080` | URL base do backend Spring Boot |
| `RPA_API_KEY` | `dev-rpa-key-change-me` | Chave enviada no header `X-Rpa-Api-Key` — **mesmo valor** que `RPA_API_KEY` no backend |
| `SOURCE_SYSTEM` | `ponto_agil` | Identificador da origem gravado em `rpa_records.source_system` |
| `HEADLESS` | `false` | `false` = navegador visível (recomendado para demonstração) |
| `SLOW_MO_MS` | `600` | Atraso entre ações do Playwright (ms) |
| `TIMEZONE` | `America/Sao_Paulo` | Fuso usado ao montar `check_in_at` / `check_out_at` |

#### Alinhamento da API key com o backend

O backend valida `POST /v1/rpa/imports` com o header `X-Rpa-Api-Key`. Antes de subir o Spring Boot, defina a mesma chave do `.env` do RPA:

```powershell
$env:RPA_API_KEY="dev-rpa-key-change-me"
mvn spring-boot:run
```

Se as chaves divergirem, a importação retorna **401**.

### Execução do RPA

#### Modo 1 — Apenas scraping (sem banco)

Útil para validar login, navegação e leitura da tabela sem depender do backend.

**Terminal A — portal mock:**

```powershell
py serve_mock.py
```

Acesse manualmente: http://localhost:5500/login.html

**Terminal B — robô:**

```powershell
.venv\Scripts\activate
py main.py --scrape-only
```

O Chromium abre em modo visível, faz login (`demo` / `demo123`), navega até **Espelho de ponto** e imprime o JSON no terminal.

#### Modo 2 — Importação completa (scraping + API + banco)

**Pré-requisitos:** backend rodando com `RPA_API_KEY` alinhada.

**Terminal 1 — backend** (pasta `registro-ponto-backend`):

```powershell
$env:RPA_API_KEY="dev-rpa-key-change-me"
mvn spring-boot:run
```

**Terminal 2 — portal mock** (esta pasta):

```powershell
py serve_mock.py
```

**Terminal 3 — RPA:**

```powershell
.venv\Scripts\activate
py main.py
```

Saída esperada no terminal: logs de cada linha lida e mensagem de sucesso com `imported_count`.

**Terminal 4 — Flutter Web** (pasta `registro-ponto-frontend`):

```powershell
flutter run -d chrome
```

Login gestor → menu **RPA** → tabela com os registros importados.

Screenshots do robô ficam em `artifacts/` (`espelho-ponto.png` em sucesso, `erro-scraping.png` em falha).

### Credenciais de teste

| Sistema | Usuário | Senha | Uso |
|---------|---------|-------|-----|
| Portal mock | `demo` | `demo123` | Login do robô no `portal-mock/` |
| Backend / Flutter (gestor) | `gerente` | `87654321` | Ver importações na aba RPA |
| Backend / Flutter (colaborador) | `colaborador` | `12345678` | App de jornadas (não usa RPA) |

### Fluxo da aplicação

O RPA **não** automatiza o Flutter. Ele lê um **sistema externo** (portal) e integra na API.

```
┌─────────────────────┐
│ Portal Ponto Ágil   │  ← mock local (portal-mock/) ou site real
│ (HTML / login)      │
└──────────┬──────────┘
           │ Playwright (browser visível)
           ▼
┌─────────────────────┐
│ registro-ponto-rpa  │  py main.py
│ scrape → normaliza  │
└──────────┬──────────┘
           │ POST /v1/rpa/imports  (X-Rpa-Api-Key)
           ▼
┌─────────────────────┐
│ registro-ponto-     │
│ backend             │  → tabela rpa_records (MySQL)
└──────────┬──────────┘
           │ GET /v1/manager/rpa/records  (JWT gerente)
           ▼
┌─────────────────────┐
│ registro-ponto-     │
│ frontend (Web)      │  /management → RPA
└─────────────────────┘
```

**Passo a passo do robô:**

1. Abre `login.html` do portal.
2. Preenche usuário e senha e entra no dashboard.
3. Clica em **Espelho de ponto** e aguarda a tabela.
4. Lê cada linha (matrícula, nome, data, entrada, saída).
5. Converte datas para ISO-8601 com fuso `America/Sao_Paulo`.
6. Envia lote para `POST /v1/rpa/imports`.

**Diferença em relação às jornadas do app:** colaboradores registram jornada no Flutter (`journeys`). O RPA importa batidas do **portal externo** para `rpa_records` — são consultas separadas.

### Portal mock

A pasta `portal-mock/` simula o Portal Ponto Ágil para desenvolvimento e demonstração ao avaliador, sem depender de conta no SaaS real.

| Arquivo | Função |
|---------|--------|
| `login.html` | Tela de login |
| `dashboard.html` | Menu após autenticação |
| `registros.html` | Espelho de ponto (tabela alvo do scrape) |
| `data/batidas.json` | Dados de demonstração (Natanael, Maria Silva) |

Credenciais do mock: `demo` / `demo123`.

Para servir sem `serve_mock.py`:

```powershell
cd portal-mock
py -m http.server 5500
```

#### Portal real (Ponto Ágil)

Quando tiver URL e credenciais do sistema real:

1. Ajuste `PORTAL_BASE_URL`, `PORTAL_USERNAME` e `PORTAL_PASSWORD` no `.env`.
2. Atualize seletores e fluxo em `src/portal/ponto_agil.py` (hoje otimizado para o mock com `data-testid`).

O mock permanece no repositório como plano B para demos reproduzíveis.

### Contrato da API (importação)

**Endpoint:** `POST {API_BASE_URL}/v1/rpa/imports`

**Header:** `X-Rpa-Api-Key: <RPA_API_KEY>`

**Body (exemplo):**

```json
{
  "source_system": "ponto_agil",
  "records": [
    {
      "external_employee_id": "001",
      "employee_name": "Natanael",
      "work_date": "2026-05-18",
      "check_in_at": "2026-05-18T08:00:00-03:00",
      "check_out_at": "2026-05-18T17:00:00-03:00",
      "raw_payload": { "matricula": "001", "nome": "Natanael" }
    }
  ]
}
```

**Resposta (201):** `{ "imported_count": 1, "ids": [1] }`

Documentação completa dos endpoints: README do `registro-ponto-backend` (secção **Registros RPA**).

### Estrutura do projeto

```
registro-ponto-rpa/
├── main.py                 # Entrada: py main.py
├── serve_mock.py           # Sobe portal mock em :5500
├── requirements.txt
├── .env.example
├── portal-mock/            # Site estático (portal externo simulado)
│   ├── login.html
│   ├── dashboard.html
│   ├── registros.html
│   ├── data/batidas.json
│   ├── css/
│   └── js/
├── artifacts/              # Screenshots (gerado em runtime; no .gitignore)
└── src/
    ├── config.py           # Settings e helpers de data/hora
    ├── models/record.py    # Modelo normalizado
    ├── portal/
    │   └── ponto_agil.py # Scraper Playwright
    ├── api/
    │   └── client.py     # Cliente HTTP → backend
    └── pipeline/
        └── run.py        # Orquestração e CLI (--scrape-only)
```

### Solução de problemas

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| `ERR_CONNECTION_REFUSED` em `:5500` | Portal mock parado | `py serve_mock.py` |
| `401` na importação | `RPA_API_KEY` diferente entre RPA e backend | Alinhar variável nos dois lados |
| `404` em `/v1/rpa/imports` | Backend antigo sem Etapa RPA | Atualizar `registro-ponto-backend` (migração V4) |
| Lista vazia no Flutter | Período filtrado só “hoje” | Ampliar datas na aba RPA ou importar registros do dia atual |
| `ZoneInfoNotFoundError` | Falta pacote `tzdata` no Windows | `pip install tzdata` (já em `requirements.txt`) |
| Tabela vazia no scrape | `batidas.json` não carregou | Servir `portal-mock/` via HTTP (não abrir `file://`) |

### Compartilhamento (avaliação)

Conforme o teste técnico, compartilhe os três repositórios com o usuário GitHub **playercontabilidade**.
