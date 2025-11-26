# 🛡️ Projeto RDT: Transporte Confiável sobre Canal Não Confiável

> **Disciplina:** Redes de Computadores  
> **Linguagem:** Python 3  

Este projeto implementa uma aplicação **Cliente-Servidor** que emula um protocolo de **Transporte Confiável de Dados (RDT)** na Camada de Aplicação. Embora utilize sockets TCP (que são confiáveis), o código trata o canal como sujeito a falhas, implementando manualmente mecanismos de recuperação de perdas e correção de erros.

O grande diferencial deste projeto é a implementação híbrida de dois algoritmos de janela deslizante: **Go-Back-N (GBN)** e **Selective Repeat (SR)**, selecionáveis em tempo de execução.

---

## 📑 Índice
1. [Funcionalidades e Requisitos](#-funcionalidades-e-requisitos)
2. [Arquitetura do Protocolo](#-arquitetura-do-protocolo)
3. [Estrutura do Pacote](#-estrutura-do-pacote)
4. [Instalação e Dependências](#-instalação-e-dependências)
5. [Guia de Execução](#-guia-de-execução)
6. [Simulação de Falhas (Testes)](#-simulação-de-falhas-testes)
7. [Detalhes Técnicos da Implementação](#-detalhes-técnicos-da-implementação)

---

## 🚀 Funcionalidades e Requisitos

Este projeto atende integralmente aos requisitos da **Entrega 3** e implementa **todos os pontos extras** sugeridos.

### ✅ Funcionalidades Principais
* **Protocolo Híbrido:** O cliente escolhe entre **Go-Back-N** ou **Selective Repeat** no início da conexão. O servidor se adapta automaticamente.
* **Handshake Inicial:** Negociação de parâmetros (Modo de Operação e Tamanho Máximo da mensagem) antes do início da transmissão.
* **Fragmentação:** Mensagens longas são divididas em pacotes com carga útil (*payload*) de **4 bytes**.
* **Temporizador (Timer):** Detecção de perda de pacotes via *timeout* no cliente (configurado para 3 segundos).
* **Feedback do Servidor:**
    * `ACK` (Positive Acknowledgment): Confirma recebimento.
    * `NACK` (Negative Acknowledgment): Informa corrupção de dados (erro de checksum).

### 🌟 Pontos Extras (Implementados)
1.  **Criptografia Simétrica (Segurança):**
    * Utiliza a biblioteca `cryptography` (algoritmo Fernet/AES).
    * O payload é criptografado no cliente e descriptografado no servidor.
    * **Chave:** Hardcoded em `criptografia.py` para fins acadêmicos (em produção seria negociada).
2.  **Checagem de Integridade (Checksum):**
    * Utiliza o algoritmo `CRC32`.
    * O servidor recalcula o checksum do payload recebido. Se diferir do cabeçalho, o pacote é descartado e um `NACK` é enviado.

---

## 🏗 Arquitetura do Protocolo

### 1. Modos de Operação

| Característica | Go-Back-N (GBN) | Selective Repeat (SR) |
| :--- | :--- | :--- |
| **Comportamento do Cliente** | Se ocorrer erro/perda no pacote N, retransmite **toda a janela** a partir de N. | Se ocorrer erro/perda no pacote N, retransmite **apenas o pacote N**. |
| **Comportamento do Servidor** | Aceita apenas pacotes na ordem correta. Descarta qualquer pacote fora de ordem. | Aceita pacotes fora de ordem e os armazena em um **buffer** até que o buraco seja preenchido. |
| **Tipo de ACK** | Cumulativo (ACK N confirma todos até N). | Individual (ACK N confirma apenas o pacote N). |

### 2. Tratamento de "Packet Sticking"
Como o TCP é um protocolo de fluxo (*stream*), múltiplas respostas do servidor (ex: `ACK0` e `ACK1`) podem chegar coladas numa única leitura do socket.
* **Solução:** O código implementa um *parser* que armazena os dados recebidos em um buffer de string e processa as mensagens separando-as pela tag `TIPO=`.

### 3. Codificação Base64
Para garantir que os dados binários criptografados (que contêm bytes ilegíveis) trafeguem com segurança dentro do nosso protocolo de texto, todo payload é codificado em **Base64** antes do envio.

---

## 📦 Estrutura do Pacote

O protocolo utiliza um cabeçalho de texto legível, separado pelo caractere `|`.

**Formato:**
`TIPO={tipo}|SEQ={id}|CHECKSUM={crc32}|PAYLOAD={dados_base64}`

* **TIPO:**
    * `MSG`: Pacote de dados contendo parte da mensagem.
    * `ACK`: Confirmação de recebimento.
    * `NACK`: Aviso de erro de integridade.
    * `EOT`: Fim de transmissão (*End of Transmission*).
* **SEQ:** Número de sequência do pacote (0, 1, 2...).
* **CHECKSUM:** Inteiro CRC32 calculado sobre os bytes originais (criptografados).
* **PAYLOAD:** Conteúdo da mensagem, criptografado e codificado em Base64.

---

## 🔧 Instalação e Dependências

**Pré-requisitos:** Python 3.8 ou superior.

1.  **Instale a biblioteca de criptografia:**
```bash
pip install cryptography
```

## 🎮 Guia de Execução

O sistema deve ser executado em dois terminais diferentes.

### Passo 1: Iniciar o Servidor
```bash
python server.py
```
O servidor ficará aguardando conexões na porta 12345.

### Passo 2: Iniciar o Cliente
```bash
python client.py 
```
### Passo 3: Interação no Cliente
1.  **IP do Servidor:** Pressione `Enter` para conectar em `localhost`.
2.  **Escolha do Protocolo:**
    * Digite `1` para usar **Go-Back-N**.
    * Digite `2` para usar **Selective Repeat**.
3.  **Tamanho Máximo:** Defina o tamanho máximo da mensagem (ex: `100`).
4.  **Mensagem:** Digite o texto a ser enviado.

---

## 🧪 Simulação de Falhas (Testes)

Para validar a lógica de recuperação (Entrega 3), o cliente possui um modo de **intervenção manual**. Antes de enviar cada pacote, ele perguntará se você deseja simular uma falha.

### Cenário A: Testar Erro de Bits (Checksum/NACK)
Este teste valida se a integridade dos dados e o NACK estão funcionando.

1.  Quando perguntado `Simular ERRO de bits no pacote X?`, digite **`s`**.
2.  **O que acontece:** O cliente inverte um bit do payload.
3.  **Resultado Esperado:**
    * Servidor detecta erro de CRC32.
    * Servidor imprime: `!!!!!!!!!!!!!!! [SEQ=X] ERRO DE CHECKSUM! Enviando NACK.`
    * Cliente recebe NACK e retransmite o pacote (ou a janela, dependendo do modo).

### Cenário B: Testar Perda de Pacote (Timeout)
Este teste valida o Temporizador e a Retransmissão Automática.

1.  Quando perguntado `Simular ERRO...?`, digite `n`.
2.  Quando perguntado `Simular PERDA do pacote X?`, digite **`s`**.
3.  **O que acontece:** O cliente **não envia** nada para o socket.
4.  **Resultado Esperado:**
    * O servidor não recebe o pacote X.
    * O cliente aguarda 3 segundos.
    * Cliente imprime: `!!! TEMPORIZADOR ESTOUROU...`.
    * Cliente retransmite o pacote (No GBN, retransmite X e todos os seguintes; no SR, apenas X).

---

## 📂 Descrição dos Arquivos

* **`server.py`**:
    * Gerencia a conexão e o handshake.
    * Implementa a lógica dupla de recepção (GBN vs SR).
    * Valida Checksum e descriptografa mensagens.
    * Mantém o buffer de reordenação (no modo SR).
* **`client.py`**:
    * Gerencia a interface de usuário e simulação de erros.
    * Fragmenta a mensagem e calcula Checksum.
    * Gerencia a janela de envio, temporizadores e retransmissões.
* **`criptografia.py`**:
    * Contém a chave simétrica.
    * Funções `encrypt()` e `decrypt()` usando Fernet.
