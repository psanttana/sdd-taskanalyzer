# Especificação SDD — TaskAnalyzer (v1.1)

Autor: Pedro Saldanha Santana — ADS, Turma A — Bootcamp III (CEUB EAD)

> **Histórico:** v1.0 (10/09/2026, Fase 1). **v1.1 (Fase 2)**: alinha nomenclatura
> da API ao desafio da Fase 2 (`analyze_tasks`, `TaskValidationError`) e explicita
> decisões antes ambíguas (ver seção 5). Alteração de assinatura registrada aqui,
> conforme exige o CONTEXT_RULES.

## 1. Propósito
Módulo de análise **read-only** que recebe uma lista de tarefas e devolve métricas:
tempo médio de conclusão, taxa de atraso e indicadores por prioridade. Não cria,
edita, exclui nem persiste tarefas.

## 2. Contrato de interface
Função principal: `analyze_tasks(tarefas: list[Tarefa]) -> Metricas`

### 2.1 Entrada — `Tarefa`
| Campo | Tipo | Obrig. | Restrições |
|---|---|---|---|
| id_tarefa | int | Sim | > 0, único na lista |
| titulo | str | Sim | não vazio / não só espaços |
| prioridade | str | Sim | "baixa", "media" ou "alta" |
| status | str | Sim | "concluida", "pendente" ou "cancelada" |
| data_criacao | datetime | Sim | UTC (timezone-aware) |
| data_inicio | datetime | Não | >= data_criacao |
| data_conclusao | datetime | Não | obrigatória se status = "concluida"; >= data_inicio |
| prazo | datetime | Sim | UTC (timezone-aware) |

### 2.2 Saída — `Metricas`
| Campo | Tipo | Descrição |
|---|---|---|
| total_tarefas | int | Total de tarefas recebidas |
| total_concluidas / total_pendentes / total_canceladas | int | Contagem por status |
| tempo_medio_conclusao_horas | float | Média (h) de início→conclusão das concluídas com ambas as datas; 0.0 se não houver |
| taxa_atraso_percentual | float | % de concluídas com data_conclusao > prazo; 2 casas; 0.0 se não houver concluídas |
| quantidade_tarefas_por_status | dict[str, int] | Sempre com as 3 chaves |
| indicadores_por_prioridade | dict[str, dict] | Para cada prioridade: `quantidade`, `tempo_medio_conclusao_horas`, `taxa_atraso_percentual` |

### 2.3 Exceção
`TaskValidationError` — única exceção de validação (datas incoerentes, valores
fora do domínio, id inválido/duplicado, título vazio, datas sem fuso).

## 3. Regras de negócio
- Só tarefas `concluida` entram em tempo médio e taxa de atraso.
- `cancelada` conta na quantidade, nunca nos cálculos.
- Concluída sem `data_inicio` é ignorada no tempo médio, mas conta na taxa de atraso e nas quantidades.
- Coerência cronológica: data_criacao ≤ data_inicio ≤ data_conclusao; senão, `TaskValidationError`.
- Divisão por zero nunca gera erro: retorna 0.0.
- Datas em UTC; conversão de fuso é responsabilidade do consumidor.
- Função pura: não modifica a entrada. Em caso de erro, nenhuma métrica parcial é retornada.

## 4. Cenários de aceite (Dado–Quando–Então)
1. **Sucesso (métricas corretas):** tarefas válidas com concluídas dentro e fora do prazo → métricas batem com o cálculo manual.
2. **Erro (datas inválidas):** `data_conclusao` < `data_criacao`/`data_inicio` (ou `data_inicio` < `data_criacao`) → `TaskValidationError` com tarefa e campo.
3. **Erro (fora do domínio):** prioridade/status inválidos → `TaskValidationError`, sem métricas parciais.
4. **Borda (sem concluídas):** médias retornam 0.0 sem exceção.
5. **Borda (lista vazia):** `Metricas` válida, contadores zerados, sem exceção.

Mapeamento para o Test Harness: `tests/test_harness.py` (`test_cenario_1_*`, `test_cenario_2_*`, `test_valores_fora_do_dominio`, `test_borda_*`).

## 5. Decisões de esclarecimento (v1.1)
- Lista vazia: `indicadores_por_prioridade` traz as 3 prioridades com valores zerados.
- Tempo médio e taxas arredondados a 2 casas.
- `quantidade` por prioridade conta **todas** as tarefas da prioridade (qualquer status); tempo e atraso usam só as concluídas daquela prioridade.
- Datas sem `tzinfo` são rejeitadas (evita comparação ambígua naive/aware).
- Nomes dos campos de dados mantêm o contrato da v1.0 (português); nomes de API pública seguem o desafio (inglês).
