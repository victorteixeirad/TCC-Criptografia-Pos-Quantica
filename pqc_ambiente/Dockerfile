# Usa uma imagem base do Ubuntu, que é compatível com apt-get
FROM ubuntu:22.04

# Define o autor e a descrição da imagem
LABEL maintainer="Victor Teixeira"
LABEL description="Ambiente para simulação de ataques a criptografia PQC com a biblioteca OQS."

# Instala as dependências de construção, git e python
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    libssl-dev \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Clone a biblioteca OQS (Open Quantum Safe) do repositório
RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git && \
    mkdir -p liboqs/build && \
    cd liboqs/build && \
    cmake .. && \
    make -j$(nproc) && \
    make install

# Copia o script de teste de ataque PQC para dentro do contêiner
COPY pqc_attack_script.sh /app/pqc_attack_script.sh

# Garante que o script seja executável
RUN chmod +x /app/pqc_attack_script.sh

# Define o diretório de trabalho
WORKDIR /app

# Comando padrão para rodar o contêiner
CMD ["/app/pqc_attack_script.sh"]