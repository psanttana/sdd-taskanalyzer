"""Test Harness do TaskAnalyzer (pytest).

Traduz os cenários de aceite da especificação (Dado-Quando-Então).
Execução: ``python -m pytest -v`` a partir da raiz do repositório.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from src.task_analyzer import Metricas, Tarefa, TaskValidationError, analyze_tasks

BASE = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)


def h(horas: float) -> datetime:
    """Retorna BASE deslocada em `horas`."""
    return BASE + timedelta(hours=horas)


def criar_tarefa(id_tarefa: int = 1, **kwargs) -> Tarefa:
    """Cria uma tarefa pendente válida, sobrescrevendo campos via kwargs."""
    dados = dict(
        id_tarefa=id_tarefa,
        titulo=f"Tarefa {id_tarefa}",
        prioridade="media",
        status="pendente",
        data_criacao=BASE,
        prazo=h(48),
    )
    dados.update(kwargs)
    return Tarefa(**dados)


@pytest.fixture
def tarefas_validas() -> list[Tarefa]:
    """Conjunto com resultado calculado manualmente (ver docstring dos testes)."""
    return [
        criar_tarefa(1, prioridade="alta", status="concluida",
                     data_inicio=h(0), data_conclusao=h(10), prazo=h(12)),
        criar_tarefa(2, prioridade="alta", status="concluida",
                     data_inicio=h(0), data_conclusao=h(20), prazo=h(12)),
        criar_tarefa(3, prioridade="media", status="concluida",
                     data_inicio=h(0), data_conclusao=h(6), prazo=h(8)),
        criar_tarefa(4, prioridade="baixa", status="concluida",
                     data_inicio=h(0), data_conclusao=h(4), prazo=h(2)),
        criar_tarefa(5, prioridade="media", status="pendente"),
        criar_tarefa(6, prioridade="baixa", status="cancelada"),
        # Concluída sem data_inicio: fora do tempo médio, mas conta no atraso
        criar_tarefa(7, prioridade="alta", status="concluida",
                     data_conclusao=h(30), prazo=h(24)),
    ]


@pytest.fixture
def tarefas_sem_concluidas() -> list[Tarefa]:
    return [
        criar_tarefa(1, status="pendente"),
        criar_tarefa(2, status="cancelada", prioridade="alta"),
    ]


@pytest.fixture
def lista_vazia() -> list[Tarefa]:
    return []


# ----------------------------- Cenário 1 ---------------------------------- #
def test_cenario_1_sucesso_metricas_gerais(tarefas_validas):
    """5 concluídas (3 atrasadas) -> 60%; tempo médio (10+20+6+4)/4 = 10h."""
    m = analyze_tasks(tarefas_validas)
    assert isinstance(m, Metricas)
    assert m.total_tarefas == 7
    assert m.total_concluidas == 5
    assert m.total_pendentes == 1
    assert m.total_canceladas == 1
    assert m.tempo_medio_conclusao_horas == 10.0
    assert m.taxa_atraso_percentual == 60.0
    assert m.quantidade_tarefas_por_status == {
        "concluida": 5, "pendente": 1, "cancelada": 1,
    }


def test_cenario_1_sucesso_indicadores_por_prioridade(tarefas_validas):
    ind = analyze_tasks(tarefas_validas).indicadores_por_prioridade
    assert ind["alta"] == {
        "quantidade": 3,
        "tempo_medio_conclusao_horas": 15.0,
        "taxa_atraso_percentual": 66.67,
    }
    assert ind["media"] == {
        "quantidade": 2,
        "tempo_medio_conclusao_horas": 6.0,
        "taxa_atraso_percentual": 0.0,
    }
    assert ind["baixa"] == {
        "quantidade": 2,
        "tempo_medio_conclusao_horas": 4.0,
        "taxa_atraso_percentual": 100.0,
    }


def test_cenario_1_canceladas_nao_entram_nos_calculos():
    tarefas = [
        criar_tarefa(1, status="concluida", data_inicio=h(0),
                     data_conclusao=h(2), prazo=h(5)),
        criar_tarefa(2, status="cancelada", data_inicio=h(0),
                     data_conclusao=h(99), prazo=h(1)),
    ]
    m = analyze_tasks(tarefas)
    assert m.tempo_medio_conclusao_horas == 2.0
    assert m.taxa_atraso_percentual == 0.0
    assert m.total_tarefas == 2


def test_funcao_pura_nao_modifica_entrada(tarefas_validas):
    copia = deepcopy(tarefas_validas)
    analyze_tasks(tarefas_validas)
    assert tarefas_validas == copia


# ----------------------------- Cenário 2 ---------------------------------- #
def test_cenario_2_conclusao_anterior_a_criacao():
    tarefa = criar_tarefa(1, status="concluida", data_criacao=h(10),
                          data_conclusao=h(5), prazo=h(20))
    with pytest.raises(TaskValidationError, match="data_conclusao"):
        analyze_tasks([tarefa])


def test_cenario_2_conclusao_anterior_ao_inicio():
    tarefa = criar_tarefa(1, status="concluida", data_inicio=h(10),
                          data_conclusao=h(5))
    with pytest.raises(TaskValidationError, match="data_conclusao"):
        analyze_tasks([tarefa])


def test_cenario_2_inicio_anterior_a_criacao():
    tarefa = criar_tarefa(1, data_criacao=h(10), data_inicio=h(5))
    with pytest.raises(TaskValidationError, match="data_inicio"):
        analyze_tasks([tarefa])


def test_cenario_2_concluida_sem_data_conclusao():
    with pytest.raises(TaskValidationError, match="obrigatória"):
        analyze_tasks([criar_tarefa(1, status="concluida")])


# ------------------- Valores fora do domínio / contrato ------------------- #
@pytest.mark.parametrize("campo,valor", [
    ("prioridade", "urgente"),
    ("status", "em_andamento"),
    ("titulo", "   "),
    ("id_tarefa", 0),
])
def test_valores_fora_do_dominio(campo, valor):
    with pytest.raises(TaskValidationError):
        analyze_tasks([Tarefa(**{**vars(criar_tarefa(1)), campo: valor})])


def test_id_duplicado():
    with pytest.raises(TaskValidationError, match="duplicado"):
        analyze_tasks([criar_tarefa(1), criar_tarefa(1)])


def test_datas_sem_fuso_sao_rejeitadas():
    tarefa = criar_tarefa(1, data_criacao=datetime(2026, 9, 1, 8, 0))
    with pytest.raises(TaskValidationError, match="UTC"):
        analyze_tasks([tarefa])


def test_erro_nao_retorna_metricas_parciais(tarefas_validas):
    tarefas_validas.append(criar_tarefa(99, prioridade="invalida"))
    with pytest.raises(TaskValidationError):
        analyze_tasks(tarefas_validas)


# ------------------------------ Casos de borda ---------------------------- #
def test_borda_sem_tarefas_concluidas(tarefas_sem_concluidas):
    m = analyze_tasks(tarefas_sem_concluidas)
    assert m.tempo_medio_conclusao_horas == 0.0
    assert m.taxa_atraso_percentual == 0.0
    assert m.total_concluidas == 0
    assert m.total_pendentes == 1


def test_borda_lista_vazia(lista_vazia):
    m = analyze_tasks(lista_vazia)
    assert m.total_tarefas == 0
    assert m.total_concluidas == 0
    assert m.total_pendentes == 0
    assert m.tempo_medio_conclusao_horas == 0.0
    assert m.taxa_atraso_percentual == 0.0
    assert m.quantidade_tarefas_por_status == {
        "concluida": 0, "pendente": 0, "cancelada": 0,
    }
    assert set(m.indicadores_por_prioridade) == {"baixa", "media", "alta"}
    assert all(i["quantidade"] == 0 and i["taxa_atraso_percentual"] == 0.0
               for i in m.indicadores_por_prioridade.values())


def test_borda_concluida_sem_inicio_nao_entra_no_tempo_medio():
    tarefa = criar_tarefa(1, status="concluida", data_conclusao=h(5), prazo=h(10))
    m = analyze_tasks([tarefa])
    assert m.tempo_medio_conclusao_horas == 0.0
    assert m.total_concluidas == 1
