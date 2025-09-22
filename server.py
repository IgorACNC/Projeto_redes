import socket

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

            dados = socket_cliente.recv(1024).decode()
            print(f"Dados recebidos do cliente: {dados}")

            try:
                tamanho_maximo = dados.split('Tamanho máximo: ')[1].split(' ')[0]
                resposta = f"Handshake OK. Modo de Operação: Modo seguro, Tamanho máximo: {tamanho_maximo} caracteres"
            except IndexError:
                resposta = "Erro: Formato de mensagem do cliente inválido."

            socket_cliente.send(resposta.encode())
            print(f"Handshake completo! Servidor enviou: {resposta}")

if __name__ == "__main__":
    iniciar_servidor()