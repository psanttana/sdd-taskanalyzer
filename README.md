# sdd-taskanalyzer

[![CI](https://github.com/psanttana/sdd-taskanalyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/psanttana/sdd-taskanalyzer/actions/workflows/ci.yml)

Módulo **TaskAnalyzer**: análise de métricas de produtividade (tempo médio de conclusão,
taxa de atraso e indicadores por prioridade), desenvolvido com **Spec-Driven Development**,
código gerado por IA sob governança (`CONTEXT_RULES.md`) e homologação humana.

Projeto cumulativo — Bootcamp III (CEUB EAD).

## Estrutura
```
sdd-taskanalyzer/
├── .github/workflows/ci.yml   # Pipeline CI (GitHub Actions)
├── Dockerfile                 # Empacotamento (python:3.11-slim)
├── docker-compose.yml         # Orquestração da suíte de testes
├── CONTEXT_RULES.md           # Governança de IA
├── specs/                     # Especificação SDD
├── tests/test_harness.py      # Testes (pytest)
├── src/task_analyzer.py       # Código gerado via IA e homologado
├── requirements.txt
└── README.md
```

## Como executar

**Local** (Python 3.11+):
```bash
pip install -r requirements.txt
python -m pytest -v
```

**Docker** (ambiente isolado):
```bash
docker build -t taskanalyzer .
docker run --rm taskanalyzer
# ou, com Compose:
docker compose run --rm tests
```

## CI/CD
O workflow `.github/workflows/ci.yml` roda a cada push ou Pull Request nas branches
`main` e `develop`: ubuntu-latest, Python 3.11, instala `requirements.txt` e executa
`pytest tests/test_harness.py -v`.

## Status
- Fase 1: especificação SDD e CONTEXT_RULES ✅
- Fase 2: código via IA, Test Harness (18 testes) e versionamento ✅
- Fase 3: CI/CD, Docker e relatório de governança ✅

Autor: Pedro Saldanha Santana — ADS, Turma A.
