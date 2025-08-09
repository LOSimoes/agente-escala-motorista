"""Interface gráfica web com Streamlit para o Agente de Escala."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from services.data_loader import preprocess_data
from models.scheduler import create_schedule
from services.exceptions_handler import apply_manual_assignments

st.set_page_config(layout="wide")

st.title("🤖 Agente de IA para Escala de Motoristas")

# --- 1. Interface de Upload na Barra Lateral ---
st.sidebar.header("Carregar Arquivos CSV")
motoristas_upload = st.sidebar.file_uploader("1. Arquivo de Motoristas", type="csv")
veiculos_upload = st.sidebar.file_uploader("2. Arquivo de Veículos", type="csv")
linhas_upload = st.sidebar.file_uploader("3. Arquivo de Linhas", type="csv")
excecoes_upload = st.sidebar.file_uploader("4. Arquivo de Exceções (Opcional)", type="csv")

st.sidebar.header("Parâmetros de Otimização")
new_driver_penalty = st.sidebar.number_input(
    "Penalidade por Novo Motorista",
    min_value=0.0,
    value=10000.0, # Valor padrão
    step=100.0,
    help="Custo artificialmente alto para desincentivar o uso de um novo motorista. Valores mais altos priorizam a reutilização dos motoristas já em rota."
)

# --- 2. Lógica de Geração da Escala (Função permanece a mesma) ---
def gerar_escala_completa(
    motoristas: pd.DataFrame,
    veiculos: pd.DataFrame,
    linhas: pd.DataFrame,
    excecoes_df: pd.DataFrame,
    penalty: float
) -> pd.DataFrame:
    """
    Executa o fluxo completo de geração de escala a partir dos dados de entrada.

    Args:
        motoristas: DataFrame com os dados dos motoristas.
        veiculos: DataFrame com os dados dos veículos.
        linhas: DataFrame com os dados das linhas.
        excecoes_df: DataFrame com as alocações manuais.
        penalty: Penalidade a ser aplicada para novos motoristas.

    Returns:
        Um DataFrame do pandas contendo a escala final gerada.
    """
    motoristas_proc, veiculos_proc, linhas_proc = preprocess_data(motoristas.copy(), veiculos.copy(), linhas.copy())
    excecoes = excecoes_df.to_dict('records')

    escala_manual, motoristas_restantes, veiculos_restantes, linhas_restantes, motoristas_agendados = \
        apply_manual_assignments(motoristas_proc, veiculos_proc, linhas_proc, excecoes)
    escala_otimizada = create_schedule(motoristas_restantes, veiculos_restantes, linhas_restantes, motoristas_agendados, new_driver_penalty=penalty)
    escala_final = {**escala_manual, **escala_otimizada}

    escala_lista = []
    for linha_id, info in sorted(escala_final.items()):
        escala_lista.append({
            'Linha_ID': linha_id,
            'Horário': info.get('horario', 'N/A'),
            'Motorista_Alocado': info.get('motorista', 'Nao Alocado'),
            'Veiculo_Alocado': info.get('veiculo', 'Nao Alocado')
        })
    return pd.DataFrame(escala_lista)

# --- 3. Lógica Principal da Interface ---
if 'df_escala' not in st.session_state:
    st.session_state.df_escala = None

if motoristas_upload and veiculos_upload and linhas_upload:
    # Carrega os dados dos arquivos enviados
    motoristas_df = pd.read_csv(motoristas_upload)
    veiculos_df = pd.read_csv(veiculos_upload)
    linhas_df = pd.read_csv(linhas_upload)

    if excecoes_upload:
        excecoes_df = pd.read_csv(excecoes_upload)
    else:
        excecoes_df = pd.DataFrame(columns=['linha', 'motorista', 'veiculo'])

    # Exibe os dados de entrada em abas
    st.header("Dados Carregados")
    tab1, tab2, tab3, tab4 = st.tabs(["Motoristas", "Veículos", "Linhas", "Exceções Manuais"])
    tab1.dataframe(motoristas_df, use_container_width=True)
    tab2.dataframe(veiculos_df, use_container_width=True)
    tab3.dataframe(linhas_df, use_container_width=True)
    tab4.dataframe(excecoes_df, use_container_width=True)

    # Botão para gerar a escala
    st.header("Geração da Escala")
    if st.button("Gerar Escala Otimizada", type="primary"):
        with st.spinner("O agente de IA está trabalhando... 🧠"):
            st.session_state.df_escala = gerar_escala_completa(motoristas_df, veiculos_df, linhas_df, excecoes_df, new_driver_penalty)

    # Exibe o resultado e o botão de download se a escala foi gerada
    if st.session_state.df_escala is not None:
        df_escala = st.session_state.df_escala
        if not df_escala.empty:
            st.success("Escala gerada com sucesso!")
            st.dataframe(df_escala, use_container_width=True)

            # Converte o DataFrame para CSV para o botão de download
            csv = df_escala.to_csv(index=False).encode('utf-8')

            st.download_button(
               label="📥 Baixar Escala como CSV",
               data=csv,
               file_name='escala_agente.csv',
               mime='text/csv',
            )
else:
    st.info("⬅️ Por favor, carregue os arquivos CSV necessários na barra lateral para começar.")