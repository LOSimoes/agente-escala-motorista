"""Módulo principal de agendamento que contém a lógica de otimização."""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from models.optimizer import calculate_distance, calculate_travel_time, calculate_travel_cost
from services.rule_engine import is_time_conflict


def create_schedule(
    motoristas: pd.DataFrame,
    veiculos: pd.DataFrame,
    linhas: pd.DataFrame,
    motoristas_agendados: Optional[Dict[str, List[Tuple[time, time, str]]]] = None,
    new_driver_penalty: float = 10000.0
) -> Dict[Any, Dict[str, Any]]:
    """
    Cria a escala otimizada de motoristas, veículos e linhas.

    Esta versão é otimizada para desempenho, pré-processando os dados e
    reduzindo a complexidade dos loops aninhados para encontrar a melhor
    combinação de motorista/veículo, minimizando o custo e o número de
    motoristas utilizados.

    Args:
        motoristas: DataFrame de motoristas disponíveis.
        veiculos: DataFrame de veículos disponíveis.
        linhas: DataFrame de linhas a serem agendadas.
        motoristas_agendados: Dicionário que rastreia os agendamentos existentes.
            Formato: {'NomeMotorista': [(inicio, fim, destino), ...]}.
        new_driver_penalty: Custo artificial para penalizar a alocação de um
            novo motorista que ainda não está em rota.

    Returns:
        Um dicionário representando a escala gerada, onde as chaves são os IDs
        das linhas e os valores são dicionários com motorista e veículo alocados.
    """
    escala_gerada = {}
    if motoristas_agendados is None:
        motoristas_agendados = {}
    veiculos_alocados = set()

    # --- Otimização 1: Pré-processamento e Estruturas de Dados Eficientes ---
    # Converter para lista de dicionários para iteração muito mais rápida que .iterrows()
    motoristas_list = motoristas.to_dict('records')

    # Criar lookups para filtragem rápida (O(M) e O(V) uma única vez)
    motoristas_por_habilidade = {}
    # Usamos defaultdict para simplificar a criação de listas
    from collections import defaultdict
    motoristas_por_habilidade = defaultdict(list)
    for m in motoristas.to_dict('records'):
        for habilidade in m.get('habilidades', []):
            motoristas_por_habilidade[habilidade].append(m)

    veiculos_por_tipo = {}
    for v in veiculos.to_dict('records'):
        tipo = v.get('tipo')
        if tipo not in veiculos_por_tipo:
            veiculos_por_tipo[tipo] = []
        veiculos_por_tipo[tipo].append(v)

    # Ordenar as linhas por horário de início e iterar sobre uma lista de dicts
    sorted_linhas = linhas.sort_values(by='horario_inicio_dt').to_dict('records')

    for linha in sorted_linhas:
        melhor_pontuacao = float('inf')
        melhor_motorista_info = None
        melhor_veiculo_info = None

        # --- Otimização 2: Filtrar candidatos antes dos loops principais ---
        tipo_veiculo_req = linha['tipo_veiculo_necessario']
        motoristas_candidatos = motoristas_por_habilidade.get(tipo_veiculo_req, [])
        veiculos_candidatos = veiculos_por_tipo.get(tipo_veiculo_req, [])

        for motorista in motoristas_candidatos:
            # Pula motoristas indisponíveis
            if motorista.get('disponibilidade', 'disponivel') != 'disponivel':
                continue

            agendamentos_atuais = motoristas_agendados.get(motorista['nome'], [])

            # Calcula o total de horas já trabalhadas pelo motorista
            horas_trabalhadas = timedelta()
            for inicio, fim, _ in agendamentos_atuais:
                inicio_dt = datetime.combine(datetime.today(), inicio)
                fim_dt = datetime.combine(datetime.today(), fim)
                if fim_dt < inicio_dt:  # Lida com turnos que cruzam a meia-noite
                    fim_dt += timedelta(days=1)
                horas_trabalhadas += (fim_dt - inicio_dt)

            # Verifica se a nova linha excede a jornada de trabalho máxima
            duracao_nova_linha = timedelta(minutes=linha['duracao_minutos'])
            jornada_maxima = timedelta(hours=motorista.get('jornada_maxima_horas', 24))
            if horas_trabalhadas + duracao_nova_linha > jornada_maxima:
                continue

            # Verifica conflito de horário direto
            agendamentos_simples = [(start, end) for start, end, dest in agendamentos_atuais]
            if is_time_conflict(linha, agendamentos_simples):
                continue

            ponto_partida_motorista = motorista['localizacao']
            horario_disponivel_motorista = datetime.min.time()
            ultimo_agendamento = max([ag for ag in agendamentos_atuais if ag[1] <= linha['horario_inicio_dt']], default=None, key=lambda x: x[1])

            if ultimo_agendamento:
                ponto_partida_motorista = ultimo_agendamento[2]  # Destino da última viagem
                horario_disponivel_motorista = ultimo_agendamento[1]  # Horário de término

            dist_deslocamento = calculate_distance(ponto_partida_motorista, linha['origem'])
            tempo_deslocamento = calculate_travel_time(dist_deslocamento)
            horario_inicio_linha_dt = datetime.combine(datetime.today(), linha['horario_inicio_dt'])
            horario_disponivel_dt = datetime.combine(datetime.today(), horario_disponivel_motorista)

            if horario_disponivel_dt + tempo_deslocamento > horario_inicio_linha_dt:
                continue

            for veiculo in veiculos_candidatos:
                if veiculo.get('disponibilidade', 'disponivel') != 'disponivel':
                    continue
                if veiculo['numero_carro'] in veiculos_alocados:
                    continue

            
            # Adiciona o novo agendamento ao "calendário" do motorista
            if melhor_motorista not in motoristas_agendados:
                motoristas_agendados[melhor_motorista] = []
            motoristas_agendados[melhor_motorista].append(
                (linha['horario_inicio_dt'], linha['horario_fim_dt'], linha['destino'])
            )
            veiculos_alocados.add(melhor_veiculo)
            
    return escala_gerada