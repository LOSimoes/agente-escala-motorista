"""Testes unitários para o módulo models/scheduler.py."""
from __future__ import annotations

from datetime import time
import pandas as pd
import pytest
from models.scheduler import create_schedule


@pytest.fixture
def base_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Cria DataFrames básicos para motoristas, veículos e linhas para uso nos testes.
    """
    motoristas = pd.DataFrame([
        # CORREÇÃO: 'habilidades' agora é uma lista
        {'nome': 'Motorista A', 'localizacao': '0,0', 'disponibilidade': 'disponivel', 'habilidades': ['simples'], 'jornada_maxima_horas': 8},
        {'nome': 'Motorista B', 'localizacao': '10,10', 'disponibilidade': 'disponivel', 'habilidades': ['simples'], 'jornada_maxima_horas': 8},
    ])
    veiculos = pd.DataFrame([
        {'numero_carro': 101, 'tipo': 'simples', 'disponibilidade': 'disponivel', 'consumo_km_l': 10},
        {'numero_carro': 102, 'tipo': 'simples', 'disponibilidade': 'disponivel', 'consumo_km_l': 10},
    ])
    linhas = pd.DataFrame([
        {'id': 'L1', 'origem': '0,0', 'destino': '5,5', 'horario_inicio': '08:00', 'horario_inicio_dt': time(8, 0), 'horario_fim_dt': time(9, 0), 'duracao_minutos': 60, 'tipo_veiculo_necessario': 'simples'},
        {'id': 'L2', 'origem': '10,10', 'destino': '15,15', 'horario_inicio': '10:00', 'horario_inicio_dt': time(10, 0), 'horario_fim_dt': time(11, 0), 'duracao_minutos': 60, 'tipo_veiculo_necessario': 'simples'},
    ])
    return motoristas, veiculos, linhas


def test_atribui_linha_simples_com_sucesso(base_data, mocker):
    """
    Testa o cenário mais básico: uma linha, um motorista e um veículo disponíveis.
    """
    # Arrange
    motoristas, veiculos, linhas = base_data
    linha_unica = linhas.head(1)

    # Mock das dependências para isolar a função create_schedule
    # REMOVIDO: validate_assignment não é mais usado
    mocker.patch('models.scheduler.calculate_travel_cost', return_value=0) # Custo zero para simplificar

    # Act
    escala = create_schedule(motoristas, veiculos, linha_unica)

    # Assert
    assert 'L1' in escala
    assert escala['L1']['motorista'] == 'Motorista A'
    assert escala['L1']['veiculo'] == 101


def test_escolhe_motorista_com_menor_custo(base_data, mocker):
    """
    Testa se o agendador escolhe o motorista com o menor custo de deslocamento.
    """
    # Arrange
    motoristas, veiculos, linhas = base_data
    linha_unica = linhas.head(1) # Linha L1 começa em '0,0'

    # Motorista A está em '0,0' (custo 0), Motorista B está em '10,10' (custo > 0)
    # REMOVIDO: validate_assignment não é mais usado
    # Simula que o custo para o Motorista A é 0 e para o B é 50
    # O side_effect precisa cobrir todas as combinações possíveis de motorista/veículo
    mocker.patch('models.scheduler.calculate_travel_cost', side_effect=[0, 0, 50, 50])

    # Act
    escala = create_schedule(motoristas, veiculos, linha_unica)

    # Assert
    assert escala['L1']['motorista'] == 'Motorista A'


def test_nao_atribui_se_houver_conflito_de_horario(base_data, mocker):
    """
    Testa se o agendador não atribui uma linha a um motorista que já está ocupado.
    """
    # Arrange
    motoristas, veiculos, linhas = base_data
    motorista_unico = motoristas.head(1) # Apenas Motorista A

    # Cria duas linhas com horários conflitantes
    linhas_conflitantes = linhas.copy()
    # Ajusta L2 para começar enquanto L1 está em andamento
    linhas_conflitantes.loc[1, 'horario_inicio_dt'] = time(8, 30)
    linhas_conflitantes.loc[1, 'horario_fim_dt'] = time(9, 30)

    # REMOVIDO: validate_assignment não é mais usado
    mocker.patch('models.scheduler.calculate_travel_cost', return_value=1)

    # Act
    escala = create_schedule(motorista_unico, veiculos, linhas_conflitantes)

    # Assert
    assert 'L1' in escala # A primeira linha deve ser agendada
    assert 'L2' not in escala # A segunda linha não deve ser agendada para o único motorista


def test_respeita_jornada_maxima_de_trabalho(base_data, mocker):
    """
    Testa se um motorista não é alocado se a linha exceder sua jornada máxima.
    """
    # Arrange
    motoristas, veiculos, linhas = base_data
    # Define uma jornada máxima muito curta para o Motorista A
    motoristas.loc[motoristas['nome'] == 'Motorista A', 'jornada_maxima_horas'] = 0.5 # 30 minutos

    linha_longa = linhas.head(1) # Linha L1 dura 60 minutos

    # REMOVIDO: validate_assignment não é mais usado
    mocker.patch('models.scheduler.calculate_travel_cost', return_value=1)

    # Act
    # Fornece apenas o Motorista A (com jornada curta) e a linha longa
    escala = create_schedule(motoristas.head(1), veiculos, linha_longa)

    # Assert
    assert 'L1' not in escala # A linha não deve ser agendada


def test_aplica_penalidade_para_novo_motorista(base_data, mocker):
    """
    Testa se o sistema prefere reutilizar um motorista (mesmo com custo de deslocamento)
    em vez de iniciar um novo, devido à penalidade.
    """
    # Arrange
    motoristas, veiculos, linhas = base_data

    # Cenário: Motorista A já fez a L1. Agora vamos agendar a L2.
    # Motorista A tem um custo de deslocamento para chegar à L2.
    # Motorista B está na origem da L2 (custo zero), mas é um "novo" motorista.

    # Pré-agenda a L1 para o Motorista A
    motoristas_agendados = {
        'Motorista A': [(time(8, 0), time(9, 0), '5,5')] # Terminou L1 em '5,5'
    }

    linha_para_agendar = linhas[linhas['id'] == 'L2'] # L2 começa em '10,10'

    # REMOVIDO: validate_assignment não é mais usado
    # Custo para Motorista A (reutilizado) ir de '5,5' para '10,10' é 10.
    # Custo para Motorista B (novo) ir de '10,10' para '10,10' é 0.
    # O side_effect precisa cobrir todas as combinações de motorista/veículo
    mocker.patch('models.scheduler.calculate_travel_cost', side_effect=[10, 10, 0, 0])

    # Act
    # A penalidade padrão (10000) é muito maior que o custo de deslocamento (10)
    escala = create_schedule(
        motoristas, veiculos, linha_para_agendar, motoristas_agendados
    )

    # Assert
    # O sistema deve escolher o Motorista A, pois 10 (custo) < 0 (custo) + 10000 (penalidade)
    assert escala['L2']['motorista'] == 'Motorista A'
