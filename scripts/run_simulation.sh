#!/bin/bash

# --- Passo 1: Construir as imagens Docker ---
echo "Construindo a imagem do ambiente RSA..."
docker build -t rsa-env ../rsa_ambiente
if [ $? -ne 0 ]; then
  echo "Erro ao construir a imagem RSA. Abortando."
  exit 1
fi

echo "Construindo a imagem do ambiente PQC..."
docker build -t pqc-env ../pqc_ambiente
if [ $? -ne 0 ]; then
  echo "Erro ao construir a imagem PQC. Abortando."
  exit 1
fi

# --- Passo 2: Rodar o contêiner RSA e coletar dados ---
echo "Iniciando a simulação para o ambiente RSA..."
docker run --name rsa_container -d --cpus=4 -m 4g rsa-env

# Monitorar o uso de recursos e tempo de execução do contêiner RSA
echo "Monitorando recursos do contêiner RSA..."
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" rsa_container > ../relatorios/rsa_stats.txt 2> /dev/null

# Aguardar a conclusão do script de ataque
docker wait rsa_container
echo "Simulação RSA concluída."

# Coletar o log de resultados
docker logs rsa_container > ../relatorios/rsa_results.log 2> /dev/null
docker rm rsa_container

# --- Passo 3: Rodar o contêiner PQC e coletar dados ---
echo "Iniciando a simulação para o ambiente PQC..."
docker run --name pqc_container -d --cpus=4 -m 4g pqc-env

# Monitorar o uso de recursos e tempo de execução do contêiner PQC
echo "Monitorando recursos do contêiner PQC..."
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" pqc_container > ../relatorios/pqc_stats.txt 2> /dev/null

# Aguardar a conclusão do script de ataque
docker wait pqc_container
echo "Simulação PQC concluída."

# Coletar o log de resultados
docker logs pqc_container > ../relatorios/pqc_results.log 2> /dev/null
docker rm pqc_container

# --- Passo 4: Coleta de Dados e Análise ---
echo "Coleta de dados de ambas as simulações concluída."
echo "Os relatórios de desempenho e logs estão na pasta 'relatorios'."

echo "---"
echo "Sumário dos Resultados:"
echo "Resultados RSA:"
cat ../relatorios/rsa_results.log
echo "---"
echo "Resultados PQC:"
cat ../relatorios/pqc_results.log