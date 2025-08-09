"""Módulo com as regras de negócio para validação de agendamentos."""
from __future__ import annotations
from datetime import time
from typing import List, Tuple


def is_time_conflict(
    novo_inicio: time,
    novo_fim: time,
    agendamentos_motorista: List[Tuple[time, time]]
) -> bool:
    """
    Verifica se o horário da nova linha conflita com os agendamentos existentes de um motorista.

    Args:
        novo_inicio: Horário de início do novo agendamento.
        novo_fim: Horário de fim do novo agendamento.
        agendamentos_motorista: Lista de tuplas (início, fim) dos agendamentos existentes.

    Returns:
        True se houver conflito, False caso contrário.
    Um conflito ocorre se (StartA < EndB) and (EndA > StartB).
    """
    for inicio_existente, fim_existente in agendamentos_motorista:
        if novo_inicio < fim_existente and novo_fim > inicio_existente:
            return True # Conflito encontrado
    return False # Sem conflitos