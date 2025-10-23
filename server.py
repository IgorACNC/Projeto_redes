import socket
import criptografia

def analisar_pacote(pacote_str):
    #Divide o pacote 'TIPO|SEQ|PAYLOAD' em suas partes.
    try:
        partes = pacote_str.split('|', 2)
        tipo = partes[0].split('=')[1]
        seq = int(partes[1].split('=')[1])
        payload = partes[2].split('=', 1)[1]
        return tipo, seq, payload
    except Exception as e:
        print(f"Erro ao analisar pacote: {e} - Pacote: {pacote_str}")
        return None, None, None

def iniciar_servidor():
    host = '0.0.0.0'
    porta = 12345

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
                resposta_handshake = f"Handshake OK. Modo: operação padrão, Tamanho máximo: {tamanho_maximo} caracteres"
            except IndexError:
                resposta_handshake = "Erro: Formato de handshake inválido."

            socket_cliente.send(resposta_handshake.encode())
            print(f"Handshake completo! Servidor enviou: {resposta_handshake}")

            print("\nIniciando recepção de mensagens...")
            mensagens_recebidas = {} 
            
            while True:
                pacote_recebido = socket_cliente.recv(1024).decode()
                if not pacote_recebido:
                    break 

                tipo, seq, payload = analisar_pacote(pacote_recebido)
                
                if tipo == "MSG":
                    try:
                        payload_descriptografado = criptografia.decrypt(payload.encode())
                    except Exception:
                        payload_descriptografado = "ERRO_DECRIPT"

                    print(f"[SEQ={seq}] Pacote recebido. Payload criptografado: {payload}")
                    print(f"[SEQ={seq}] Payload descriptografado: {payload_descriptografado}")
                    
                    mensagens_recebidas[seq] = payload_descriptografado
                    
                    ack = f"TIPO=ACK|SEQ={seq}"
                    socket_cliente.send(ack.encode())

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

            print("Recepção de mensagens finalizada. Fechando conexão com o cliente.")

if __name__ == "__main__":
    iniciar_servidor()