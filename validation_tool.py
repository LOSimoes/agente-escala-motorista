"""Ferramenta de linha de comando para comparar duas escalas."""
from __future__ import annotations

import pandas as pd
import sys


def compare_scales(real_scale_path: str, agent_scale_path: str) -> None:
    """
    Compara uma escala real com a escala gerada pelo agente e destaca as diferenças.

    Args:
        real_scale_path: O caminho para o arquivo CSV da escala real (humana).
        agent_scale_path: O caminho para o arquivo CSV da escala gerada pelo agente.
    """
    try:
        df_real = pd.read_csv(real_scale_path)
        df_agent = pd.read_csv(agent_scale_path)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e.filename}")
        return

    # Renomeia colunas para a comparação
    df_real = df_real.rename(columns={'Motorista_Alocado': 'Motorista_Real', 'Veiculo_Alocado': 'Veiculo_Real'})
    df_agent = df_agent.rename(columns={'Motorista_Alocado': 'Motorista_Agente', 'Veiculo_Alocado': 'Veiculo_Agente'})

    # Junta as duas escalas pela Linha_ID
    df_comparison = pd.merge(df_real[['Linha_ID', 'Motorista_Real', 'Veiculo_Real']],
                             df_agent[['Linha_ID', 'Motorista_Agente', 'Veiculo_Agente']],
                             on='Linha_ID',  # Corrigido de 'on' para 'on'
                             how='outer') # 'outer' para ver linhas que um pode ter e o outro não

    # Encontra as divergências
    divergences = df_comparison[
        (df_comparison['Motorista_Real'] != df_comparison['Motorista_Agente']) |
        (df_comparison['Veiculo_Real'] != df_comparison['Veiculo_Agente'])
    ].fillna('N/A')

    print("--- Análise Comparativa de Escalas ---")
    print("\nMétricas Gerais:")
    print(f"  - Motoristas únicos (Real):   {df_real['Motorista_Real'].nunique()}")
    print(f"  - Motoristas únicos (Agente): {df_agent['Motorista_Agente'].nunique()}")

    if divergences.empty:
        print("\n✅ As escalas são idênticas!")
    else:
        print(f"\nEncontradas {len(divergences)} divergências:")
        print(divergences.to_string(index=False))

if __name__ == "__main__":
    # Exemplo de como usar: python validation_tool.py data/escala_real.csv data/escala_agente.csv
    if len(sys.argv) != 3:
        print("Uso: python validation_tool.py <caminho_escala_real> <caminho_escala_agente>")
    else:
        compare_scales(sys.argv[1], sys.argv[2])