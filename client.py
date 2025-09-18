import socket

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

        while True:
            try:
                tamanho_maximo = int(input("Digite o tamanho máximo de caracteres desejado (mínimo 30): "))
                if tamanho_maximo >= 30:
                    break
                else:
                    print("Valor inválido. O tamanho máximo deve ser no mínimo 30.")
            except ValueError:
                print("Entrada inválida. Por favor, digite um número.")
        
        dados_para_enviar = f"Modo: operação padrão, Tamanho máximo: {tamanho_maximo} caracteres"
        
        socket_cliente.send(dados_para_enviar.encode())
        print(f"Cliente enviou: {dados_para_enviar}")

        resposta = socket_cliente.recv(1024).decode()
        print(f"Resposta do servidor: {resposta}")


if __name__ == "__main__":
    iniciar_cliente()