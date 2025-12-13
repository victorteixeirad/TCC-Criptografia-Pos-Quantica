#!/bin/bash
# run_simulation.sh - roda N simulações para RSA e PQC e salva resultados por rodada
# Uso: ./run_simulation.sh N
# Ex: ./run_simulation.sh 5

set -euo pipefail

NUM_RUNS=${1:-1}   # Se não passar argumento, roda 1 vez
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(realpath "${SCRIPT_DIR}/..")"
REL_DIR="${ROOT_DIR}/relatorios"

RSA_IMG_PATH="${ROOT_DIR}/rsa_ambiente"
PQC_IMG_PATH="${ROOT_DIR}/pqc_ambiente"

RSA_IMAGE_TAG="rsa-env"
PQC_IMAGE_TAG="pqc-env"

# Certifica-se que a pasta de relatórios existe
mkdir -p "${REL_DIR}"

echo "=== Iniciando pipeline de simulação — ${NUM_RUNS} rodadas ==="

# Build das imagens (apenas 1 vez)
echo "Construindo imagem RSA..."
docker build -t "${RSA_IMAGE_TAG}" "${RSA_IMG_PATH}" || { echo "Falha no build RSA"; exit 1; }

echo "Construindo imagem PQC..."
docker build -t "${PQC_IMAGE_TAG}" "${PQC_IMG_PATH}" || { echo "Falha no build PQC"; exit 1; }

for run in $(seq 1 "${NUM_RUNS}"); do
  echo "---------------------------------------------"
  echo "Rodada ${run} / ${NUM_RUNS}"
  timestamp=$(date +%Y%m%d_%H%M%S)
  
  # --- RSA ---
  rsa_container_name="rsa_container_run${run}_${timestamp}"
  echo "Iniciando container RSA (${rsa_container_name})..."
  docker run --name "${rsa_container_name}" -d --cpus=4 -m 4g "${RSA_IMAGE_TAG}"
  
  echo "Coletando snapshot de stats RSA..."
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "${rsa_container_name}" > "${REL_DIR}/rsa_stats_${run}.txt" 2>/dev/null || true

  docker wait "${rsa_container_name}" >/dev/null
  echo "Container RSA finalizado. Salvando logs..."
  docker logs "${rsa_container_name}" > "${REL_DIR}/rsa_results_${run}.log" 2>/dev/null || true
  docker rm "${rsa_container_name}" >/dev/null || true

  # --- PQC ---
  pqc_container_name="pqc_container_run${run}_${timestamp}"
  echo "Iniciando container PQC (${pqc_container_name})..."
  docker run --name "${pqc_container_name}" -d --cpus=4 -m 4g "${PQC_IMAGE_TAG}"
  
  echo "Coletando snapshot de stats PQC..."
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "${pqc_container_name}" > "${REL_DIR}/pqc_stats_${run}.txt" 2>/dev/null || true

  docker wait "${pqc_container_name}" >/dev/null
  echo "Container PQC finalizado. Salvando logs..."
  docker logs "${pqc_container_name}" > "${REL_DIR}/pqc_results_${run}.log" 2>/dev/null || true
  docker rm "${pqc_container_name}" >/dev/null || true

  echo "Rodada ${run} concluída. Arquivos gerados em ${REL_DIR}:"
  ls -1 "${REL_DIR}"/rsa_*_"${run}".* "${REL_DIR}"/pqc_*_"${run}".* 2>/dev/null || true
done

echo "Todas as rodadas finalizadas. Chamando o analisador Python para agregar resultados..."
# Chame o analisador (assume python3 no PATH)
python3 "${SCRIPT_DIR}/analyze_performance.py" --aggregate || true

echo "Pipeline concluído. Verifique a pasta ${REL_DIR} para os resultados."
