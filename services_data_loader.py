import pandas as pd
from datetime import datetime, timedelta

def load_data(file_path):
    return pd.read_csv(file_path)

def preprocess_data(motoristas, veiculos, linhas):
    # Pré-processamento de Habilidades
    if 'habilidades' in motoristas.columns:
        motoristas['habilidades'] = motoristas['habilidades'].apply(lambda x: [h.strip() for h in str(x).split(',')])

    # Pré-processamento de Horários
    if 'horario_inicio' in linhas.columns and 'duracao_minutos' in linhas.columns:
        # Converte a string 'HH:MM' para um objeto time
        linhas['horario_inicio_dt'] = pd.to_datetime(linhas['horario_inicio'], format='%H:%M').dt.time
        # Calcula o horário de término
        linhas['horario_fim_dt'] = linhas.apply(lambda x: (datetime.combine(datetime.today(), x['horario_inicio_dt']) + timedelta(minutes=x['duracao_minutos'])).time(), axis=1)

    return motoristas, veiculos, linhas