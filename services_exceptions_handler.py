"""Módulo para lidar com alocações manuais (exceções) na escala."""
from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple
import pandas as pd
from datetime import time


def apply_manual_assignments(
    motoristas: pd.DataFrame,
    veiculos: pd.DataFrame,
    linhas: pd.DataFrame,
    excecoes: List[Dict[str, Any]]
) -> Tuple[Dict[Any, Dict[str, Any]], pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, List[Tuple[time, time, str]]]]:
    """
    Aplica as exceções manuais antes da otimização.

    Args:
        motoristas: DataFrame com todos os motoristas.
        veiculos: DataFrame com todos os veículos.
        linhas: DataFrame com todas as linhas.
        excecoes: Lista de dicionários, onde cada um representa uma alocação manual.

    Returns:
        Uma tupla contendo:
        - escala_manual: Dicionário com as alocações manuais.
        - motoristas_restantes: DataFrame de motoristas para o otimizador.
        - veiculos_restantes: DataFrame de veículos disponíveis.
        - linhas_restantes: DataFrame de linhas a serem agendadas.
        - motoristas_agendados_manualmente: Dicionário com os horários já ocupados.
    """
    escala_manual = {}
    motoristas_agendados_manualmente = {}
    veiculos_usados = set()
    linhas_usadas = set()

    for excecao in excecoes:
        linha_id = excecao['linha']
        motorista_nome = excecao['motorista']
        veiculo_numero = excecao.get('veiculo')

        # Encontra a linha correspondente para obter os horários
        linha_info_series = linhas[linhas['id'] == linha_id]
        if linha_info_series.empty:
            print(f"Aviso: Linha ID {linha_id} da exceção não encontrada. Pulando.")
            continue
        linha_info = linha_info_series.iloc[0]

        escala_manual[linha_id] = {
            'motorista': motorista_nome,
            'veiculo': veiculo_numero,
            'horario': linha_info['horario_inicio']
        }
        
        linhas_usadas.add(linha_id)
        
        # Adiciona o agendamento manual ao calendário do motorista
        if motorista_nome not in motoristas_agendados_manualmente:
            motoristas_agendados_manualmente[motorista_nome] = []
        # Adiciona o destino ao agendamento para rastrear a localização final
        motoristas_agendados_manualmente[motorista_nome].append(
            (linha_info['horario_inicio_dt'], linha_info['horario_fim_dt'], linha_info['destino'])
        )

        if veiculo_numero:
            veiculos_usados.add(veiculo_numero)

    # Filtra os dataframes para remover os recursos já alocados manualmente
    # Nota: Não removemos mais o motorista, pois ele pode estar disponível para outros horários.
    motoristas_restantes = motoristas
    veiculos_restantes = veiculos[~veiculos['numero_carro'].isin(veiculos_usados)]
    linhas_restantes = linhas[~linhas['id'].isin(linhas_usadas)]

    return escala_manual, motoristas_restantes, veiculos_restantes, linhas_restantes, motoristas_agendados_manualmente