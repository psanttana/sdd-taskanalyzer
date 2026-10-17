# sdd-taskanalyzer

Módulo **TaskAnalyzer**: análise de métricas de produtividade (tempo médio de conclusão,
taxa de atraso e indicadores por prioridade), desenvolvido com **Spec-Driven Development**
e código gerado por IA sob governança (`CONTEXT_RULES.md`) e homologação humana.

Projeto cumulativo — Bootcamp III (CEUB EAD) · Fase 2.

## Estrutura
```
sdd-taskanalyzer/
├── README.md
├── CONTEXT_RULES.md
├── .gitignore
├── requirements.txt
├── specs/task_analyzer_spec.md
├── tests/test_harness.py
└── src/task_analyzer.py
```

## Como executar
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -v
```
Requer Python 3.11+.

## Uso
```python
from datetime import datetime, timezone
from src.task_analyzer import Tarefa, analyze_tasks

t = Tarefa(1, "Exemplo", "alta", "concluida",
           data_criacao=datetime(2026, 9, 1, 8, tzinfo=timezone.utc),
           prazo=datetime(2026, 9, 2, 8, tzinfo=timezone.utc),
           data_inicio=datetime(2026, 9, 1, 9, tzinfo=timezone.utc),
           data_conclusao=datetime(2026, 9, 1, 15, tzinfo=timezone.utc))
print(analyze_tasks([t]).tempo_medio_conclusao_horas)  # 6.0
```

## Status
Fase 2: 18 testes, 100% aprovados, 100% de cobertura. Fase 3 (CI/CD, Docker): pendente.

Autor: Pedro Saldanha Santana — ADS, Turma A.
