"""Módulo TaskAnalyzer: análise read-only de métricas de produtividade.

Recebe uma lista de tarefas e devolve indicadores objetivos (tempo médio de
conclusão, taxa de atraso e indicadores por prioridade). É stateless, não
persiste dados e não modifica a lista de entrada.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

PRIORIDADES_VALIDAS: tuple[str, ...] = ("baixa", "media", "alta")
STATUS_VALIDOS: tuple[str, ...] = ("concluida", "pendente", "cancelada")
SEGUNDOS_POR_HORA: float = 3600.0


class TaskValidationError(Exception):
    """Erro de validação dos dados de entrada de uma tarefa.

    Disparado para datas incoerentes, valores fora do domínio permitido,
    identificadores inválidos/duplicados ou títulos vazios.
    """


@dataclass(frozen=True)
class Tarefa:
    """Tarefa de entrada, conforme o contrato da Seção 1.3.1 da especificação.

    Attributes:
        id_tarefa: Identificador único (> 0).
        titulo: Texto descritivo (não vazio).
        prioridade: "baixa", "media" ou "alta".
        status: "concluida", "pendente" ou "cancelada".
        data_criacao: Criação da tarefa (UTC, timezone-aware).
        prazo: Data limite de entrega (UTC, timezone-aware).
        data_inicio: Início da execução (opcional).
        data_conclusao: Conclusão (obrigatória se status == "concluida").
    """

    id_tarefa: int
    titulo: str
    prioridade: str
    status: str
    data_criacao: datetime
    prazo: datetime
    data_inicio: Optional[datetime] = None
    data_conclusao: Optional[datetime] = None


@dataclass(frozen=True)
class Metricas:
    """Resultado da análise (contrato da Seção 1.3.2 da especificação)."""

    total_tarefas: int
    total_concluidas: int
    total_pendentes: int
    total_canceladas: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float
    quantidade_tarefas_por_status: dict[str, int] = field(default_factory=dict)
    indicadores_por_prioridade: dict[str, dict[str, float]] = field(
        default_factory=dict
    )


# --------------------------------------------------------------------------- #
# Validação
# --------------------------------------------------------------------------- #
def _validar_datas_aware(tarefa: Tarefa) -> None:
    """Garante que todas as datas informadas possuem timezone (UTC)."""
    campos = {
        "data_criacao": tarefa.data_criacao,
        "prazo": tarefa.prazo,
        "data_inicio": tarefa.data_inicio,
        "data_conclusao": tarefa.data_conclusao,
    }
    for nome, valor in campos.items():
        if valor is not None and valor.tzinfo is None:
            raise TaskValidationError(
                f"Tarefa {tarefa.id_tarefa}: campo '{nome}' deve conter fuso (UTC)."
            )


def _validar_ordem_cronologica(tarefa: Tarefa) -> None:
    """Valida data_criacao <= data_inicio <= data_conclusao."""
    criacao, inicio, conclusao = (
        tarefa.data_criacao,
        tarefa.data_inicio,
        tarefa.data_conclusao,
    )
    if inicio is not None and inicio < criacao:
        raise TaskValidationError(
            f"Tarefa {tarefa.id_tarefa}: 'data_inicio' anterior a 'data_criacao'."
        )
    if conclusao is not None and conclusao < criacao:
        raise TaskValidationError(
            f"Tarefa {tarefa.id_tarefa}: 'data_conclusao' anterior a 'data_criacao'."
        )
    if inicio is not None and conclusao is not None and conclusao < inicio:
        raise TaskValidationError(
            f"Tarefa {tarefa.id_tarefa}: 'data_conclusao' anterior a 'data_inicio'."
        )


def _validar_tarefa(tarefa: Tarefa) -> None:
    """Valida uma única tarefa; lança TaskValidationError se inválida."""
    if not isinstance(tarefa.id_tarefa, int) or tarefa.id_tarefa <= 0:
        raise TaskValidationError(
            f"Tarefa com id inválido ({tarefa.id_tarefa!r}): deve ser inteiro > 0."
        )
    if not isinstance(tarefa.titulo, str) or not tarefa.titulo.strip():
        raise TaskValidationError(
            f"Tarefa {tarefa.id_tarefa}: 'titulo' não pode ser vazio."
        )
    if tarefa.prioridade not in PRIORIDADES_VALIDAS:
        raise TaskValidationError(
            f"Tarefa {tarefa.id_tarefa}: prioridade inválida ({tarefa.prioridade!r})."
        )
    if tarefa.status not in STATUS_VALIDOS:
        raise TaskValidationError(
            f"Tarefa {tarefa.id_tarefa}: status inválido ({tarefa.status!r})."
        )
    _validar_datas_aware(tarefa)
    if tarefa.status == "concluida" and tarefa.data_conclusao is None:
        raise TaskValidationError(
            f"Tarefa {tarefa.id_tarefa}: 'data_conclusao' é obrigatória "
            "para tarefas concluídas."
        )
    _validar_ordem_cronologica(tarefa)


def _validar_tarefas(tarefas: list[Tarefa]) -> None:
    """Valida todas as tarefas e a unicidade dos identificadores."""
    ids_vistos: set[int] = set()
    for tarefa in tarefas:
        _validar_tarefa(tarefa)
        if tarefa.id_tarefa in ids_vistos:
            raise TaskValidationError(f"id_tarefa duplicado: {tarefa.id_tarefa}.")
        ids_vistos.add(tarefa.id_tarefa)


# --------------------------------------------------------------------------- #
# Cálculos
# --------------------------------------------------------------------------- #
def _calcular_tempo_medio_horas(concluidas: list[Tarefa]) -> float:
    """Tempo médio (h) entre início e conclusão; 0.0 se não houver elegíveis."""
    duracoes = [
        (t.data_conclusao - t.data_inicio).total_seconds() / SEGUNDOS_POR_HORA
        for t in concluidas
        if t.data_inicio is not None and t.data_conclusao is not None
    ]
    if not duracoes:
        return 0.0
    return round(sum(duracoes) / len(duracoes), 2)


def _calcular_taxa_atraso(concluidas: list[Tarefa]) -> float:
    """Percentual de concluídas após o prazo; 0.0 se não houver concluídas."""
    if not concluidas:
        return 0.0
    atrasadas = sum(1 for t in concluidas if t.data_conclusao > t.prazo)
    return round(atrasadas / len(concluidas) * 100, 2)


def _somente_concluidas(tarefas: list[Tarefa]) -> list[Tarefa]:
    """Filtra tarefas com status 'concluida'."""
    return [t for t in tarefas if t.status == "concluida"]


def _contar_por_status(tarefas: list[Tarefa]) -> dict[str, int]:
    """Conta tarefas por status, incluindo status com contagem zero."""
    contagem = {status: 0 for status in STATUS_VALIDOS}
    for tarefa in tarefas:
        contagem[tarefa.status] += 1
    return contagem


def _indicadores_por_prioridade(
    tarefas: list[Tarefa],
) -> dict[str, dict[str, float]]:
    """Calcula quantidade, tempo médio e taxa de atraso por prioridade."""
    resultado: dict[str, dict[str, float]] = {}
    for prioridade in PRIORIDADES_VALIDAS:
        do_grupo = [t for t in tarefas if t.prioridade == prioridade]
        concluidas = _somente_concluidas(do_grupo)
        resultado[prioridade] = {
            "quantidade": len(do_grupo),
            "tempo_medio_conclusao_horas": _calcular_tempo_medio_horas(concluidas),
            "taxa_atraso_percentual": _calcular_taxa_atraso(concluidas),
        }
    return resultado


# --------------------------------------------------------------------------- #
# API pública
# --------------------------------------------------------------------------- #
def analyze_tasks(tarefas: list[Tarefa]) -> Metricas:
    """Analisa uma lista de tarefas e retorna as métricas de produtividade.

    Função pura: não altera a lista de entrada nem persiste dados.

    Args:
        tarefas: Lista de tarefas a analisar (pode ser vazia).

    Returns:
        Objeto Metricas com totais, tempo médio, taxa de atraso e indicadores
        por prioridade.

    Raises:
        TaskValidationError: Se alguma tarefa violar o contrato de entrada.
    """
    logger.info("Iniciando análise de %d tarefa(s).", len(tarefas))
    _validar_tarefas(tarefas)

    concluidas = _somente_concluidas(tarefas)
    por_status = _contar_por_status(tarefas)
    metricas = Metricas(
        total_tarefas=len(tarefas),
        total_concluidas=por_status["concluida"],
        total_pendentes=por_status["pendente"],
        total_canceladas=por_status["cancelada"],
        tempo_medio_conclusao_horas=_calcular_tempo_medio_horas(concluidas),
        taxa_atraso_percentual=_calcular_taxa_atraso(concluidas),
        quantidade_tarefas_por_status=por_status,
        indicadores_por_prioridade=_indicadores_por_prioridade(tarefas),
    )
    logger.info("Análise concluída com sucesso.")
    return metricas
