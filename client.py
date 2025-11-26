import socket
import criptografia
import zlib
import random
import time
import base64 

TEMPO_LIMITE_SEGUNDOS = 3 

def calcular_checksum(dados_bytes):
    return zlib.crc32(dados_bytes)

def analisar_pacote(pacote_str):
    if "TIPO=" in pacote_str[1:]:
        pacote_str = pacote_str.split("TIPO=")[0]

    try:
        partes = pacote_str.split('|', 2)
        tipo = partes[0].split('=')[1]
        seq = int(partes[1].split('=')[1])
        return tipo, seq
    except Exception as e:
        print(f"Erro ao analisar pacote: {e} - Pacote: {pacote_str}")
        return None, None

def simular_erro_bits(pacote_bytes):
    try:
        pos_payload = pacote_bytes.rfind(b'PAYLOAD=') + len(b'PAYLOAD=')
        if pos_payload == -1 + len(b'PAYLOAD='):
             return pacote_bytes 

        indice_corromper = random.randint(pos_payload, len(pacote_bytes) - 1)
        byte_original = pacote_bytes[indice_corromper]
        novo_byte_int = (byte_original + 1) % 256 
        pacote_corrompido = bytearray(pacote_bytes)
        pacote_corrompido[indice_corromper] = novo_byte_int
        
        print(f"*** ERRO SIMULADO: Bit corrompido no índice {indice_corromper} ***")
        return bytes(pacote_corrompido)
    except Exception as e:
        print(f"Erro ao simular corrupção: {e}")
        return pacote_bytes

def iniciar_cliente():
    host = input("Digite o IP do servidor (ou pressione Enter para 'localhost'): ")
    if not host:
        host = 'localhost'
    porta = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_cliente:
        try:
            socket_cliente.connect((host, porta))
        except ConnectionRefusedError:
            print(f"Erro: A conexão com {host}:{porta} foi recusada. O servidor está online?")
            return
        
        socket_cliente.setblocking(False)

        modo_escolhido = ""
        while True:
            try:
                socket_cliente.setblocking(True)
                print("\nEscolha o protocolo de janela deslizante:")
                print("1 - Go-Back-N (GBN)")
                print("2 - Selective Repeat (SR)")
                opcao = input("Opção: ")
                socket_cliente.setblocking(False)
                
                if opcao == '1':
                    modo_escolhido = "GBN"
                    break
                elif opcao == '2':
                    modo_escolhido = "SR"
                    break
                else:
                    print("Opção inválida.")
            except ValueError:
                pass

        tamanho_maximo_handshake = 0
        while True:
            try:
                socket_cliente.setblocking(True)
                tamanho_maximo_handshake = int(input("Digite o tamanho máximo de caracteres da comunicação (mínimo 30): "))
                socket_cliente.setblocking(False)
                if tamanho_maximo_handshake >= 30:
                    break
                else:
                    print("Valor inválido. Mínimo 30.")
            except ValueError:
                print("Digite um número.")

        dados_handshake = f"Modo: {modo_escolhido}, Tamanho máximo: {tamanho_maximo_handshake} caracteres"
        
        socket_cliente.setblocking(True)
        socket_cliente.send(dados_handshake.encode())
        print(f"Cliente enviou handshake: {dados_handshake}")

        resposta_handshake = socket_cliente.recv(1024).decode()
        print(f"Resposta do servidor: {resposta_handshake}")
        if "Erro" in resposta_handshake:
            print("Handshake falhou. Encerrando.")
            return
        
        try:
            JANELA_TAM = int(resposta_handshake.split('JANELA_TAM=')[1])
            print(f"Tamanho da janela definido pelo servidor: {JANELA_TAM}")
        except Exception:
            JANELA_TAM = 5
            
        socket_cliente.setblocking(False) 

        mensagem_completa = ""
        while True:
            socket_cliente.setblocking(True)
            mensagem_completa = input(f"\nDigite a mensagem a ser enviada (limite {tamanho_maximo_handshake}): ")
            socket_cliente.setblocking(False) 
            
            if len(mensagem_completa) == 0:
                print("Vazia.")
            elif len(mensagem_completa) > tamanho_maximo_handshake:
                print(f"Erro: Excede {tamanho_maximo_handshake}.")
            else:
                break
        
        TAMANHO_PAYLOAD = 4
        chunks = [mensagem_completa[i:i + TAMANHO_PAYLOAD] for i in range(0, len(mensagem_completa), TAMANHO_PAYLOAD)]
        print(f"Mensagem fragmentada em {len(chunks)} pacotes.")
        
        todos_pacotes_preparados = {}
        for i, chunk in enumerate(chunks):
            payload_criptografado_bytes = criptografia.encrypt(chunk)
            checksum = calcular_checksum(payload_criptografado_bytes)
            payload_b64_str = base64.b64encode(payload_criptografado_bytes).decode('ascii')
            pacote_str = f"TIPO=MSG|SEQ={i}|CHECKSUM={checksum}|PAYLOAD={payload_b64_str}"
            todos_pacotes_preparados[i] = pacote_str.encode()

        base = 0 
        prox_seq_num = 0 
        timer_inicio = 0 
        buffer_recebimento = ""
        pacotes_com_erro_simulado = set() 
        acks_recebidos_sr = set() 

        print(f"\n--- Iniciando Transmissão em Modo {modo_escolhido} ---")

        while base < len(chunks):
            
            while prox_seq_num < base + JANELA_TAM and prox_seq_num < len(chunks):
                
                if modo_escolhido == "SR" and prox_seq_num in acks_recebidos_sr:
                    prox_seq_num += 1
                    continue

                pacote_bytes = todos_pacotes_preparados[prox_seq_num]
                
                # Simulação de Erros/Perdas
                simular_erro = 'n'
                simular_perda = 'n'
                if prox_seq_num not in pacotes_com_erro_simulado: 
                    socket_cliente.setblocking(True)
                    print(f"--- Pacote {prox_seq_num} ---")
                    simular_erro = input(f"Simular ERRO de bits no pacote {prox_seq_num}? (s/n): ").lower()
                    if simular_erro != 's':
                        simular_perda = input(f"Simular PERDA do pacote {prox_seq_num}? (s/n): ").lower()
                    socket_cliente.setblocking(False) 
                
                if simular_erro == 's':
                    print(f"Enviando [SEQ={prox_seq_num}] (COM ERRO SIMULADO)...")
                    socket_cliente.send(simular_erro_bits(pacote_bytes))
                    pacotes_com_erro_simulado.add(prox_seq_num)
                elif simular_perda == 's':
                    print(f"Enviando [SEQ={prox_seq_num}] (SIMULANDO PERDA)...")
                    pacotes_com_erro_simulado.add(prox_seq_num) 
                else:
                    print(f"Enviando [SEQ={prox_seq_num}]...")
                    socket_cliente.send(pacote_bytes)
                
                if base == prox_seq_num and timer_inicio == 0:
                    timer_inicio = time.time()
                
                prox_seq_num += 1

            try:
                buffer_recebimento += socket_cliente.recv(1024).decode()
            except BlockingIOError:
                pass

            while "TIPO=" in buffer_recebimento and "|" in buffer_recebimento:
                try:
                    inicio_pacote = buffer_recebimento.find("TIPO=")
                    fim_pacote = buffer_recebimento.find("TIPO=", inicio_pacote + 1)
                    
                    pacote_completo = ""
                    if fim_pacote == -1:
                        pacote_completo = buffer_recebimento[inicio_pacote:]
                        buffer_recebimento = ""
                    else:
                        pacote_completo = buffer_recebimento[inicio_pacote:fim_pacote]
                        buffer_recebimento = buffer_recebimento[fim_pacote:]

                    # print(f"DEBUG: Recebido {pacote_completo}") # Descomente para debug
                    tipo_resp, seq_resp = analisar_pacote(pacote_completo)
                    
                    if tipo_resp == "ACK":
                        if modo_escolhido == "GBN":
                            
                            print(f"[GBN] ACK cumulativo recebido para [SEQ={seq_resp}].")
                            base = max(base, seq_resp + 1)
                            if base == prox_seq_num:
                                timer_inicio = 0
                            else:
                                timer_inicio = time.time() # Reinicia timer para o próximo da base

                        elif modo_escolhido == "SR":
                            print(f"[SR] ACK individual recebido para [SEQ={seq_resp}].")
                            acks_recebidos_sr.add(seq_resp)
                        
                            while base in acks_recebidos_sr and base < len(chunks):
                                base += 1
                                timer_inicio = 0 
                                if base < prox_seq_num:
                                    timer_inicio = time.time()

                    elif tipo_resp == "NACK":
                        if modo_escolhido == "GBN":
                            print(f"!!! [GBN] NACK recebido para [SEQ={seq_resp}]. Retransmitindo janela...")
                            prox_seq_num = base 
                            timer_inicio = 0 
                        elif modo_escolhido == "SR":
                            print(f"!!! [SR] NACK recebido para [SEQ={seq_resp}]. Retransmitindo APENAS este pacote...")
                            socket_cliente.send(todos_pacotes_preparados[seq_resp])

                except Exception as e:
                    print(f"Erro buffer: {e}")
                    buffer_recebimento = ""

            # Verificar Timeout
            if timer_inicio != 0 and (time.time() - timer_inicio) > TEMPO_LIMITE_SEGUNDOS:
                if modo_escolhido == "GBN":
                    print(f"!!! [GBN] TEMPORIZADOR ESTOUROU para [BASE={base}]. Retransmitindo janela...")
                    timer_inicio = 0
                    prox_seq_num = base # Recua para a base
                
                elif modo_escolhido == "SR":
                    print(f"!!! [SR] TEMPORIZADOR ESTOUROU para [BASE={base}]. Retransmitindo pacote {base}...")
                    # No SR simplificado, se estourar o timer da base, retransmitimos a base
                    socket_cliente.send(todos_pacotes_preparados[base])
                    timer_inicio = time.time() # Reinicia o timer para este pacote

        print("\nTodos os pacotes de dados foram confirmados.")
        
        print("Enviando sinal de Fim de Transmissão (EOT)...")
        socket_cliente.setblocking(True) 
        eot_pacote = f"TIPO=EOT|SEQ={len(chunks)}|CHECKSUM=0|PAYLOAD=NULL"
        socket_cliente.send(eot_pacote.encode())
        
        while True:
            try:
                ack_final = socket_cliente.recv(1024).decode()
                if "TIPO=ACK" in ack_final:
                    print(f"ACK final recebido: {ack_final}")
                    break
            except socket.timeout:
                socket_cliente.send(eot_pacote.encode())
        
        print("\nMensagem completa enviada e confirmada.")

if __name__ == "__main__":
    iniciar_cliente()