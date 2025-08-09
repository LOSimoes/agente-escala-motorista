# Agente de IA para Escala de Motoristas

Este projeto é um assistente digital inteligente projetado para automatizar e otimizar a complexa tarefa de montar escalas de motoristas para empresas de fretamento. Utilizando um conjunto de regras e heurísticas de otimização, o agente analisa motoristas, veículos e linhas para criar a escala mais eficiente possível, minimizando custos e ociosidade.

## Funcionalidades Principais

- **Otimização Inteligente:** O agente vai além da simples distância, calculando o **custo real** de cada deslocamento com base no consumo de combustível do veículo.
- **Minimização de Recursos:** Prioriza a reutilização de motoristas que já estão em rota, aplicando uma penalidade ajustável para "chamar" um novo motorista, reduzindo assim o número total de pessoal necessário por dia.
- **Encadeamento de Viagens:** Otimiza a rota dos motoristas, permitindo que comecem uma nova viagem a partir do ponto final da anterior, minimizando deslocamentos ociosos.
- **Respeito às Regras de Negócio:**
  - Valida as **habilidades** do motorista para o veículo necessário.
  - Respeita a **jornada máxima de trabalho** de cada motorista.
  - Verifica a **disponibilidade** de motoristas e veículos (marcando-os como "em manutenção", por exemplo).
- **Flexibilidade com Exceções:** Permite que o analista de escala defina alocações manuais (exceções) que o agente trata como prioridade máxima, ajustando o restante da escala de forma inteligente.
- **Interface Gráfica Interativa:** Oferece uma interface web (criada com Streamlit) onde o analista pode carregar os arquivos de dados, ajustar parâmetros de otimização e visualizar a escala gerada em tempo real.

## Como Funciona: O Modelo de Dados

O agente opera com base em arquivos CSV que devem ser preenchidos com os dados da operação.

- **`data/motoristas.csv`**: Contém as informações dos motoristas.
  - `chapa`: Identificador único do motorista.
  - `nome`: Nome completo.
  - `localizacao`: Coordenadas da residência (ex: "-23.55,-46.63").
  - `regiao`: Região onde mora (ex: "Zona Sul").
  - `habilidades`: Tipos de veículo que pode dirigir (ex: "simples,articulado").
  - `disponibilidade`: `disponivel` ou `indisponivel`.
  - `jornada_maxima_horas`: Limite de horas de trabalho no dia.

- **`data/veiculos.csv`**: Contém as informações da frota.
  - `numero_carro`: Identificador único do veículo (placa ou frota).
  - `tipo`: `simples` ou `articulado`.
  - `consumo_km_l`: Eficiência de combustível (km por litro).
  - `disponibilidade`: `disponivel` ou `manutencao`.

- **`data/linhas.csv`**: Contém as informações das rotas a serem percorridas.
  - `id`: Identificador único da linha.
  - `origem`, `destino`: Coordenadas de partida e chegada.
  - `horario_inicio`: Horário de início no formato `HH:MM`.
  - `duracao_minutos`: Duração total da viagem em minutos.

- **`data/excecoes.csv`**: Alocações manuais que devem ser respeitadas.
  - `linha`: ID da linha.
  - `motorista`: Nome do motorista a ser alocado.
  - `veiculo`: Número do carro a ser alocado.

## Como Usar: Interface Gráfica (Recomendado)

### 1. Configurar o Ambiente
É altamente recomendado usar um ambiente virtual para isolar as dependências do projeto.

```bash
# Navegue até a pasta do projeto
cd /caminho/para/projAssEscala

# Crie o ambiente virtual
python3 -m venv .venv

# Ative o ambiente
source .venv/bin/activate
```

### 2. Instalar as Dependências
Com o ambiente ativo, instale as bibliotecas necessárias a partir do arquivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 3. Executar a Aplicação
Inicie a interface web com o seguinte comando:

```bash
streamlit run app.py
```

### 4. Gerar a Escala
Na interface que abrirá no seu navegador:
1.  Use a barra lateral para fazer o upload dos seus arquivos CSV (`motoristas`, `veiculos`, `linhas` e, opcionalmente, `excecoes`).
2.  Ajuste os parâmetros de otimização, como a "Penalidade por Novo Motorista".
3.  Clique no botão **"Gerar Escala Otimizada"**.
4.  A escala final será exibida na tela e poderá ser baixada como um arquivo CSV.

## Como "Treinar" e Calibrar o Agente

O agente não é treinado como um modelo de Machine Learning, mas sim **calibrado** para que suas decisões se alinhem com as de um analista experiente. O processo é cíclico:

1.  **Coletar Dados Históricos:** Pegue os arquivos de entrada (`motoristas.csv`, etc.) de um dia real e a escala final que foi **executada por um humano** nesse dia. Salve a escala humana como `data/escala_real.csv`.

2.  **Gerar a Escala do Agente:** Use a interface para carregar os mesmos arquivos de entrada e gerar uma escala. Baixe o resultado como `data/escala_agente.csv`.

3.  **Comparar com a Ferramenta de Validação:** Use o script `validation_tool.py` para obter um relatório detalhado das diferenças.

    ```bash
    python validation_tool.py data/escala_real.csv data/escala_agente.csv
    ```

4.  **Analisar e Ajustar:** Analise o relatório.
    - **O agente usou mais motoristas que o real?** Aumente a "Penalidade por Novo Motorista" na interface para forçar a reutilização.
    - **O agente escolheu um motorista/veículo diferente do analista?** Verifique os custos. Talvez o preço do combustível (`FUEL_PRICE_PER_LITER` em `models/optimizer.py`) precise de ajuste, ou talvez exista uma regra de negócio não documentada que precise ser adicionada ao código.

5.  **Repetir:** Volte ao passo 2 com os parâmetros ajustados e gere uma nova escala. Repita o ciclo até que o resultado do agente seja satisfatório e confiável.