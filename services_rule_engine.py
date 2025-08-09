def validate_assignment(motorista, veiculo, linha):
    # Verifica se o motorista tem a habilidade para o tipo de veículo
    if linha['tipo_veiculo_necessario'] not in motorista['habilidades']:
        return False
    if veiculo['tipo'] != linha['tipo_veiculo_necessario']:
        return False
    return True

def is_time_conflict(nova_linha, agendamentos_motorista):
    """
    Verifica se o horário da nova linha conflita com os agendamentos existentes de um motorista.
    Um conflito ocorre se (StartA < EndB) and (EndA > StartB).
    """
    novo_inicio = nova_linha['horario_inicio_dt']
    novo_fim = nova_linha['horario_fim_dt']

    for inicio_existente, fim_existente in agendamentos_motorista:
        if novo_inicio < fim_existente and novo_fim > inicio_existente:
            return True # Conflito encontrado
    return False # Sem conflitos