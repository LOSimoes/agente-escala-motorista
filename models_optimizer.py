from datetime import timedelta
import pandas as pd

# Assume 1 unidade de distância leva 5 minutos para viajar.
# Este valor pode ser ajustado para refletir a velocidade média real.
AVG_MINUTES_PER_DISTANCE_UNIT = 5.0
FUEL_PRICE_PER_LITER = 5.50 # Exemplo: R$ 5,50 por litro
NEW_DRIVER_PENALTY = 10000.0 # Custo artificialmente alto para desincentivar o uso de um novo motorista

def calculate_distance(loc1, loc2):
    # loc1 e loc2 são strings: "-23.55,-46.63"
    lat1, lon1 = map(float, loc1.split(','))
    lat2, lon2 = map(float, loc2.split(','))
    return ((lat1 - lat2)**2 + (lon1 - lon2)**2) ** 0.5

def calculate_travel_time(distance):
    """Converte a distância em um objeto timedelta."""
    return timedelta(minutes=distance * AVG_MINUTES_PER_DISTANCE_UNIT)

def calculate_travel_cost(distance, vehicle):
    """Calcula o custo monetário de um deslocamento ocioso."""
    # Se o veículo não tiver dados de consumo, o custo é a própria distância (fallback)
    if 'consumo_km_l' not in vehicle or pd.isna(vehicle['consumo_km_l']) or vehicle['consumo_km_l'] <= 0:
        return distance
    
    liters_needed = distance / vehicle['consumo_km_l']
    cost = liters_needed * FUEL_PRICE_PER_LITER
    return cost