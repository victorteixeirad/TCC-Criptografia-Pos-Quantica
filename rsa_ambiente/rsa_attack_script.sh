#!/bin/bash

echo "Iniciando simulação de ataque e fatoração contra criptografia RSA..."

# ----------------------------------------------------
# OPERAÇÃO INICIAL: GERAÇÃO DA CHAVE RSA (O alvo do ataque)
# ----------------------------------------------------
openssl genrsa -out rsa_key.pem 2048
echo "Chave RSA de 2048 bits gerada com sucesso. (2048-bit é o alvo)"
echo "----------------------------------------------------"

START_TIME=$(date +%s)
TOTAL_ATTEMPTS=20000000 # Mantido para 20 milhões
ATTEMPTS_REPORT=5000000

# Função para simular trabalho intensivo (fatoração)
run_attack_simulation() {
    # Roda uma fração do trabalho
    for i in $(seq 1 $(($TOTAL_ATTEMPTS / 4))); do
        # Simula tentativas de "ataque"
        if [ $((i % ($ATTEMPTS_REPORT / 4))) -eq 0 ]; then
            ELAPSED_TIME=$(( $(date +%s) - START_TIME ))
            echo "  -- Progresso: $((($1 + 1) * 25))% completo. Tentativas totais: $((($1 + 1) * $ATTEMPTS_REPORT)). Tempo decorrido: ${ELAPSED_TIME}s."
        fi
    done
}

# Executa 4 processos de ataque em paralelo para usar múltiplos núcleos
echo "Iniciando 4 processos de ataque paralelos para maximizar o uso da CPU..."
for j in $(seq 0 3); do
    run_attack_simulation $j & 
done

# Aguarda todos os processos em background terminarem
wait

END_TIME=$(date +%s)
ELAPSED_TIME=$((END_TIME - START_TIME))

echo "Ataque concluído."
echo "Tempo total de execução do ataque exaustivo: ${ELAPSED_TIME} segundos."
echo "Simulação de sucesso da fatoração. Chave RSA COMPROMETIDA."

# Salva os resultados em um arquivo de log
echo "Tempo de Execução (s): ${ELAPSED_TIME}" > /app/attack_results.log
echo "Status do Ataque: COMPROMETIDA" >> /app/attack_results.log