from cryptography.fernet import Fernet

# Esta é a chave simétrica. DEVE ser a mesma no cliente e no servidor
CHAVE = b'K3YnJ-Y9Yv1hX9sPqGfXvB-tYwZ8x7cE1qF6rN0k2aA='

cifrador = Fernet(CHAVE)

def encrypt(mensagem):
    #Criptografa uma mensagem (string) e retorna bytes
    mensagem_bytes = mensagem.encode()
    return cifrador.encrypt(mensagem_bytes)

def decrypt(token):
    #Descriptografa um token (bytes) e retorna uma string
    try:
        dados_descriptografados = cifrador.decrypt(token)
        return dados_descriptografados.decode()
    except Exception as e:
        print(f"Erro ao descriptografar: {e}")
        return "ERRO_DECRIPT"