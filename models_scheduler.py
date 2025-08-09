from models.optimizer import calculate_distance, calculate_travel_time, calculate_travel_cost
from services.rule_engine import validate_assignment, is_time_conflict
from datetime import datetime, timedelta
import pandas as pd

def create_schedule(motoristas, veiculos, linhas, motoristas_agendados=None, new_driver_penalty=10000.0):
    escala_gerada = {}
    if motoristas_agendados is None:
        # Dicionário para rastrear horários: {'Nome': [(inicio, fim, destino), ...]}
        motoristas_agendados = {}
    veiculos_alocados = set()

    # Ordenar as linhas por horário de início para um agendamento mais lógico
    for _, linha in linhas.sort_values(by='horario_inicio_dt').iterrows():
        melhor_pontuacao = float('inf')
        melhor_motorista = None
        melhor_veiculo = None

        for _, motorista in motoristas.iterrows():
            # Pula motoristas indisponíveis
            if motorista['disponibilidade'] != 'disponivel':
                continue
            
            agendamentos_atuais = motoristas_agendados.get(motorista['nome'], [])

            # Calcula o total de horas já trabalhadas pelo motorista
            horas_trabalhadas = timedelta()
            for inicio, fim, _ in agendamentos_atuais:
                inicio_dt = datetime.combine(datetime.today(), inicio)
                fim_dt = datetime.combine(datetime.today(), fim)
                if fim_dt < inicio_dt: # Lida com turnos que cruzam a meia-noite
                    fim_dt += timedelta(days=1)
                horas_trabalhadas += (fim_dt - inicio_dt)

            # Verifica se a nova linha excede a jornada de trabalho máxima
            duracao_nova_linha = timedelta(minutes=linha['duracao_minutos'])
            jornada_maxima = timedelta(hours=motorista.get('jornada_maxima_horas', 24)) # Padrão de 24h se não especificado
            if horas_trabalhadas + duracao_nova_linha > jornada_maxima:
                continue

            # Verifica conflito de horário direto
            agendamentos_simples = [(start, end) for start, end, dest in agendamentos_atuais]
            if is_time_conflict(linha, agendamentos_simples):
                continue

            # Determina a localização e o horário de disponibilidade do motorista
            ponto_partida_motorista = motorista['localizacao']
            horario_disponivel_motorista = datetime.min.time()

            # Encontra a última viagem do motorista que termina antes da nova linha começar
            ultimo_agendamento = max([ag for ag in agendamentos_atuais if ag[1] <= linha['horario_inicio_dt']], default=None, key=lambda x: x[1])

            if ultimo_agendamento:
                ponto_partida_motorista = ultimo_agendamento[2]  # Destino da última viagem
                horario_disponivel_motorista = ultimo_agendamento[1] # Horário de término da última viagem

            # Calcula o custo (distância de deslocamento) e verifica se há tempo suficiente
            dist_deslocamento = calculate_distance(ponto_partida_motorista, linha['origem'])
            tempo_deslocamento = calculate_travel_time(dist_deslocamento)

            horario_inicio_linha_dt = datetime.combine(datetime.today(), linha['horario_inicio_dt'])
            horario_disponivel_dt = datetime.combine(datetime.today(), horario_disponivel_motorista)

            # Se o motorista não consegue chegar a tempo, pula para o próximo
            if horario_disponivel_dt + tempo_deslocamento > horario_inicio_linha_dt:
                continue

            for _, veiculo in veiculos.iterrows():
                # Pula veículos indisponíveis (em manutenção)
                if veiculo.get('disponibilidade', 'disponivel') != 'disponivel':
                    continue

                # Pula veículos já alocados
                if veiculo['numero_carro'] in veiculos_alocados:
                    continue

                if validate_assignment(motorista, veiculo, linha):
                    # Calcula o custo do deslocamento com base no veículo específico
                    custo_deslocamento = calculate_travel_cost(dist_deslocamento, veiculo)

                    # Adiciona uma penalidade alta se for necessário usar um novo motorista
                    custo_final = custo_deslocamento
                    if motorista['nome'] not in motoristas_agendados:
                        custo_final += new_driver_penalty
                    
                    if custo_final < melhor_pontuacao:
                        melhor_pontuacao = custo_final
                        melhor_motorista = motorista['nome']
                        melhor_veiculo = veiculo['numero_carro']

        if melhor_motorista and melhor_veiculo:
            escala_gerada[linha['id']] = {'motorista': melhor_motorista, 'veiculo': melhor_veiculo, 'horario': linha['horario_inicio']}
            
            # Adiciona o novo agendamento ao "calendário" do motorista
            if melhor_motorista not in motoristas_agendados:
                motoristas_agendados[melhor_motorista] = []
            motoristas_agendados[melhor_motorista].append(
                (linha['horario_inicio_dt'], linha['horario_fim_dt'], linha['destino'])
            )
            veiculos_alocados.add(melhor_veiculo)
            
    return escala_gerada