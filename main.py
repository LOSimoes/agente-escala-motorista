"""Ponto de entrada principal para executar o agente de escala via linha de comando."""
import sys
import os
import pandas as pd

# Adiciona o diretório raiz do projeto ao sys.path para resolver importações locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_loader import load_data, preprocess_data
from models.scheduler import create_schedule
from services.exceptions_handler import apply_manual_assignments

if __name__ == "__main__":
    # 1. Carregar e pré-processar os dados
    motoristas = load_data('data/motoristas.csv')
    veiculos = load_data('data/veiculos.csv')
    linhas = load_data('data/linhas.csv')
    motoristas, veiculos, linhas = preprocess_data(motoristas, veiculos, linhas)

    # 2. Carregar exceções de um arquivo CSV
    excecoes = []
    try:
        # Usamos o pandas para carregar o CSV e convertê-lo para o formato de lista de dicionários
        df_excecoes = pd.read_csv('data/excecoes.csv')
        excecoes = df_excecoes.to_dict('records')
    except FileNotFoundError:
        print("Info: Arquivo 'data/excecoes.csv' não encontrado. A escala será gerada sem exceções manuais.")
    except Exception as e:
        print(f"Aviso: Ocorreu um erro ao ler o arquivo de exceções: {e}")
        
    # 3. Aplicar as exceções primeiro, separando os recursos já alocados
    escala_manual, motoristas_restantes, veiculos_restantes, linhas_restantes, motoristas_agendados = \
        apply_manual_assignments(motoristas, veiculos, linhas, excecoes)

    # 4. Rodar o otimizador apenas com os recursos restantes
    escala_otimizada = create_schedule(motoristas_restantes, veiculos_restantes, linhas_restantes, motoristas_agendados)

    # 5. Combinar as escalas manual e otimizada para o resultado final
    escala_final = {**escala_manual, **escala_otimizada}
    
    print("\n--- Escala Final Gerada ---")
    for linha_id, info in sorted(escala_final.items()):
        print(f"Linha {linha_id} ({info.get('horario', 'N/A')}): Motorista {info.get('motorista', 'N/A')} - Veículo {info.get('veiculo', 'N/A')}")

    # 6. Salvar a escala final em um arquivo CSV para o analista
    try:
        escala_para_salvar = []
        for linha_id, info in sorted(escala_final.items()):
            escala_para_salvar.append({
                'Linha_ID': linha_id,
                'Horario': info.get('horario', 'N/A'),
                'Motorista_Alocado': info.get('motorista', 'Nao Alocado'),
                'Veiculo_Alocado': info.get('veiculo', 'Nao Alocado')
            })
        df_final = pd.DataFrame(escala_para_salvar)
        df_final.to_csv('data/escala_final.csv', index=False)
        print("\n[SUCESSO] A escala foi salva em 'data/escala_final.csv'")
    except Exception as e:
        print(f"\n[ERRO] Não foi possível salvar o arquivo da escala final: {e}")