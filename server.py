import socket
import criptografia
import zlib
import base64

def analisar_pacote_com_checksum(pacote_str):
    try:
        partes = pacote_str.split('|', 3)
        tipo = partes[0].split('=')[1]
        seq = int(partes[1].split('=')[1])
        checksum_recebido = int(partes[2].split('=')[1])
        payload = partes[3].split('=', 1)[1]
        return tipo, seq, checksum_recebido, payload
    except Exception as e:
        print(f"Erro ao analisar pacote: {e} - Pacote: {pacote_str}")
        return None, None, None, None

def calcular_checksum(dados_bytes):
    return zlib.crc32(dados_bytes)

def iniciar_servidor():
    host = '0.0.0.0'
    porta = 12345
    TAMANHO_JANELA_SERVIDOR = 5 

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_servidor:
        socket_servidor.bind((host, porta))
        socket_servidor.listen(1)
        print(f"Servidor aguardando conexão em {host}:{porta}...")

        socket_cliente, endereco_cliente = socket_servidor.accept()
        
        with socket_cliente:
            print(f"Conexão estabelecida com {endereco_cliente}")

            dados_handshake = socket_cliente.recv(1024).decode()
            print(f"Dados de handshake recebidos: {dados_handshake}")

            try:
                tamanho_maximo = dados_handshake.split('Tamanho máximo: ')[1].split(' ')[0]
                resposta_handshake = f"Handshake OK. Modo: GBN. TamMax: {tamanho_maximo}. JANELA_TAM={TAMANHO_JANELA_SERVIDOR}"
            except IndexError:
                resposta_handshake = "Erro: Formato de handshake inválido."

            socket_cliente.send(resposta_handshake.encode())
            print(f"Handshake completo! Servidor enviou: {resposta_handshake}")

            print("\nIniciando recepção de mensagens (Modo Go-Back-N)...")
            mensagens_recebidas = {}
            seq_esperado = 0
            
            while True:
                pacote_recebido = socket_cliente.recv(1024).decode()
                if not pacote_recebido:
                    break 

                pacotes = pacote_recebido.split('TIPO=')
                for pacote_str in pacotes:
                    if not pacote_str:
                        continue
                    
                    tipo, seq, checksum_recebido, payload_b64 = analisar_pacote_com_checksum("TIPO=" + pacote_str)
                    if tipo is None:
                        continue

                    if tipo == "MSG":
                        
                        try:
                            payload_bytes = base64.b64decode(payload_b64)
                        except Exception as e:
                            print(f"Erro ao decodificar Base64: {e}. Descartando pacote.")
                            continue

                        checksum_calculado = calcular_checksum(payload_bytes)
                        if seq == seq_esperado:
                            if checksum_calculado == checksum_recebido:
                                print(f"[SEQ={seq}] Pacote recebido NA ORDEM. Enviando ACK={seq}.")
                                try:
                                    payload_descriptografado = criptografia.decrypt(payload_bytes)
                                    mensagens_recebidas[seq] = payload_descriptografado
                                except Exception:
                                    mensagens_recebidas[seq] = "ERRO_DECRIPT"
                                
                                ack = f"TIPO=ACK|SEQ={seq_esperado}"
                                socket_cliente.send(ack.encode())
                                seq_esperado += 1
                            
                            else:
                                print(f"!!!!!!!!!!!!!!! [SEQ={seq}] ERRO DE CHECKSUM! Enviando NACK. !!!!!!!!!!!!!!!")
                                nack = f"TIPO=NACK|SEQ={seq_esperado}"
                                socket_cliente.send(nack.encode())
                        
                        else:
                            print(f"[SEQ={seq}] Pacote FORA DE ORDEM (Esperando {seq_esperado}). Descartando.")
                            ack_anterior = f"TIPO=ACK|SEQ={seq_esperado - 1}"
                            socket_cliente.send(ack_anterior.encode())

                    elif tipo == "EOT":
                        print(f"\n[SEQ={seq}] Recebido sinal de Fim de Transmissão (EOT).")
                        ack = f"TIPO=ACK|SEQ={seq}"
                        socket_cliente.send(ack.encode())
                        
                        print("--- MENSAGEM COMPLETA RECEBIDA ---")
                        mensagem_completa = ""
                        for i in sorted(mensagens_recebidas.keys()):
                            mensagem_completa += mensagens_recebidas[i]
                        
                        print(mensagem_completa)
                        print("------------------------------------")
                        break 
                
                if "EOT" in pacote_recebido:
                    break

            print("Recepção de mensagens finalizada. Fechando conexão com o cliente.")

if __name__ == "__main__":
    iniciar_servidor()