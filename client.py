import socket
import criptografia

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


        tamanho_maximo_handshake = 0
        while True:
            try:
                tamanho_maximo_handshake = int(input("Digite o tamanho máximo de caracteres da comunicação (mínimo 30): "))
                if tamanho_maximo_handshake >= 30:
                    break
                else:
                    print("Valor inválido. O tamanho máximo deve ser no mínimo 30.")
            except ValueError:
                print("Entrada inválida. Por favor, digite um número.")
        
        dados_handshake = f"Modo: operação padrão, Tamanho máximo: {tamanho_maximo_handshake} caracteres"
        
        socket_cliente.send(dados_handshake.encode())
        print(f"Cliente enviou handshake: {dados_handshake}")

        resposta_handshake = socket_cliente.recv(1024).decode()
        print(f"Resposta do servidor: {resposta_handshake}")
        if "Erro" in resposta_handshake:
            print("Handshake falhou. Encerrando.")
            return

        mensagem_completa = ""
        while True:
            mensagem_completa = input(f"\nDigite a mensagem a ser enviada (limite de {tamanho_maximo_handshake} caracteres): ")
            if len(mensagem_completa) == 0:
                print("A mensagem não pode estar vazia.")
            elif len(mensagem_completa) > tamanho_maximo_handshake:
                print(f"Erro: A mensagem excede o tamanho máximo de {tamanho_maximo_handshake} caracteres.")
            else:
                break
        
        TAMANHO_PAYLOAD = 4
        
        chunks = [mensagem_completa[i:i + TAMANHO_PAYLOAD] for i in range(0, len(mensagem_completa), TAMANHO_PAYLOAD)]
        
        print(f"Mensagem fragmentada em {len(chunks)} pacotes.")
        seq_num = 0
        
        for chunk in chunks:
            payload_criptografado_bytes = criptografia.encrypt(chunk)
            payload_criptografado_str = payload_criptografado_bytes.decode()

            pacote = f"TIPO=MSG|SEQ={seq_num}|PAYLOAD={payload_criptografado_str}"
            
            print(f"\nEnviando [SEQ={seq_num}]: Carga útil original: '{chunk}'")
            socket_cliente.send(pacote.encode())
            
            ack_recebido = socket_cliente.recv(1024).decode()
            
            print(f"ACK recebido do servidor: {ack_recebido}")

            tipo_ack, seq_ack, _ = analisar_pacote(ack_recebido)
            if tipo_ack == "ACK" and seq_ack == seq_num:
                print(f"[SEQ={seq_num}] confirmado com sucesso.")
                seq_num += 1
            else:
                print(f"Erro: ACK inesperado ou mal formatado: {ack_recebido}")

        print("\nEnviando sinal de Fim de Transmissão (EOT)...")
        eot_pacote = f"TIPO=EOT|SEQ={seq_num}|PAYLOAD=NULL"
        socket_cliente.send(eot_pacote.encode())

        ack_final = socket_cliente.recv(1024).decode()
        print(f"ACK final recebido: {ack_final}")
        
        print("\nMensagem completa enviada e confirmada.")

def analisar_pacote(pacote_str):
    try:
        partes = pacote_str.split('|', 2)
        tipo = partes[0].split('=')[1]
        seq = int(partes[1].split('=')[1])
        payload = partes[2].split('=', 1)[1] if len(partes) > 2 else None
        return tipo, seq, payload
    except Exception as e:
        print(f"Erro ao analisar pacote: {e} - Pacote: {pacote_str}")
        return None, None, None

if __name__ == "__main__":
    iniciar_cliente()