# Usa uma imagem base do Ubuntu para ter um ambiente limpo e familiar.
FROM ubuntu:22.04

# Define o autor e a descrição da imagem.
LABEL maintainer="Victor Teixeira"
LABEL description="Ambiente para simulação de ataques a criptografia RSA."

# Instala as ferramentas necessárias para os testes.
RUN apt-get update && apt-get install -y \
    openssl \
    git \
    build-essential \
    cmake \
    libssl-dev \
    libcurl4-openssl-dev \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copia o script de teste de ataque para dentro do contêiner.
COPY rsa_attack_script.sh /app/rsa_attack_script.sh

# Garante que o script seja executável.
RUN chmod +x /app/rsa_attack_script.sh

# Define o diretório de trabalho.
WORKDIR /app

# Comando padrão para rodar o contêiner.
CMD ["/app/rsa_attack_script.sh"]