"""Módulo com funções de cálculo para otimização de rotas."""
from __future__ import annotations

from datetime import timedelta
import pandas as pd

AVG_MINUTES_PER_DISTANCE_UNIT = 5.0
FUEL_PRICE_PER_LITER = 5.50 # Exemplo: R$ 5,50 por litro
NEW_DRIVER_PENALTY = 10000.0 # Custo artificialmente alto para desincentivar o uso de um novo motorista

def calculate_distance(loc1, loc2):
    # loc1 e loc2 são strings: "-23.55,-46.63"
    lat1, lon1 = map(float, loc1.split(','))
    lat2, lon2 = map(float, loc2.split(','))
    return ((lat1 - lat2)**2 + (lon1 - lon2)**2) ** 0.5


def calculate_distance(loc1: str, loc2: str) -> float:
    """
    Calcula a distância euclidiana entre duas coordenadas.

    As coordenadas são fornecidas como strings no formato "latitude,longitude".

    Args:
        loc1: A primeira coordenada (ex: "-23.55,-46.63").
        loc2: A segunda coordenada (ex: "-23.55,-46.63").

    Returns:
        A distância calculada como um float.
    """
    lat1, lon1 = map(float, loc1.split(','))
    lat2, lon2 = map(float, loc2.split(','))
    return ((lat1 - lat2)**2 + (lon1 - lon2)**2)**0.5


def calculate_travel_time(distance: float) -> timedelta:
    """
    Converte uma distância em um tempo de viagem estimado.

    Args:
        distance: A distância a ser convertida.

    Returns:
        Um objeto timedelta representando o tempo de viagem.
    """
    return timedelta(minutes=distance * AVG_MINUTES_PER_DISTANCE_UNIT)


def calculate_travel_cost(distance: float, vehicle: pd.Series) -> float:
    """
    Calcula o custo monetário de um deslocamento com base no consumo do veículo.

    Args:
        distance: A distância do deslocamento.
        vehicle: Uma Series do pandas contendo os dados do veículo.

    Returns:
        O custo monetário do deslocamento. Se os dados de consumo não estiverem
        disponíveis, retorna a própria distância como um custo de fallback.
    """
    if 'consumo_km_l' not in vehicle or pd.isna(vehicle['consumo_km_l']) or vehicle['consumo_km_l'] <= 0:
        return distance

    liters_needed = distance / vehicle['consumo_km_l']
    cost = liters_needed * FUEL_PRICE_PER_LITER
    return cost