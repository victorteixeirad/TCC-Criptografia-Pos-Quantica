#!/usr/bin/env python3
import os
import re
import argparse
import json
import csv
from tabulate import tabulate
import matplotlib.pyplot as plt
from statistics import mean, stdev

# --- Definições de Caminho ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_RELATORIOS = os.path.join(BASE_DIR, "..", "relatorios")
PASTA_RELATORIOS = os.path.normpath(PASTA_RELATORIOS)

# --- Funções utilitárias ---

def converter_unidade(valor_str):
    if not valor_str:
        return valor_str
    valor_str = valor_str.strip()
    match = re.match(r"([\d\.]+)(GiB|MiB|KiB|B|GB|MB|kB)", valor_str)
    if not match:
        return valor_str

    valor, unidade = float(match.group(1)), match.group(2)

    if unidade in ("GiB", "GB"):
        return f"{valor:.2f} GB"
    elif unidade in ("MiB", "MB"):
        return f"{(valor / 1024):.2f} GB"
    elif unidade == "KiB" or unidade == "kB":
        return f"{(valor / (1024 * 1024)):.2f} GB"
    elif unidade == "B":
        return f"{(valor / (1024 * 1024 * 1024)):.2f} GB"
    return valor_str

def extrair_numero_tempo(conteudo):
    tempo = re.search(r"Tempo total de execução.*?(\d+)\s*segundos", conteudo)
    if tempo:
        return int(tempo.group(1))
    return None

def extrair_status(conteudo, tipo):
    if tipo == "rsa":
        return "COMPROMETIDA" if re.search(r"Chave RSA COMPROMETIDA", conteudo, re.IGNORECASE) else "FALHA"
    else:
        return "RESISTENTE" if re.search(r"Criptografia PQC demonstrou resistência", conteudo, re.IGNORECASE) else "FALHA"

def parse_stats_file(caminho_stats):
    try:
        with open(caminho_stats, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception:
        return None

    m = re.search(r"[\S]+\s+([\d\.]+)\%\s+([\d\.]+(?:MiB|GiB|MB|GB|KiB|kB|B))\s*/\s*([\d\.]+(?:GiB|GB|MiB))", conteudo)
    if not m:
        m2 = re.search(r"([\d\.]+)\%\s+([\d\.]+(?:MiB|GiB|MB|GB|KiB|kB|B))", conteudo)
        if m2:
            cpu = float(m2.group(1))
            mem_raw = m2.group(2)
            mem_conv = converter_unidade(mem_raw)
            try:
                mem_gb = float(re.search(r"([\d\.]+)", mem_conv).group(1))
            except:
                mem_gb = None
            return {"cpu": cpu, "mem_gb": mem_gb}
        return None

    cpu = float(m.group(1))
    mem_raw = m.group(2)
    mem_conv = converter_unidade(mem_raw)
    try:
        mem_gb = float(re.search(r"([\d\.]+)", mem_conv).group(1))
    except:
        mem_gb = None

    return {"cpu": cpu, "mem_gb": mem_gb}

def coletar_arquivos_por_padrao(padrao_prefixo):
    files = []
    for f in os.listdir(PASTA_RELATORIOS):
        if f.startswith(padrao_prefixo):
            files.append(os.path.join(PASTA_RELATORIOS, f))
    def extract_index(path):
        base = os.path.basename(path)
        m = re.search(r"_(\d+)\.log$|_(\d+)\.txt$", base)
        if m:
            for g in m.groups():
                if g:
                    return int(g)
        return base
    try:
        files_sorted = sorted(files, key=extract_index)
    except Exception:
        files_sorted = sorted(files)
    return files_sorted

def agrupar_por_rodada():
    rsa_logs = coletar_arquivos_por_padrao("rsa_results_")
    pqc_logs = coletar_arquivos_por_padrao("pqc_results_")
    rsa_stats = coletar_arquivos_por_padrao("rsa_stats_")
    pqc_stats = coletar_arquivos_por_padrao("pqc_stats_")

    def idx_from_name(path):
        base = os.path.basename(path)
        m = re.search(r"_(\d+)\.", base)
        return int(m.group(1)) if m else None

    runs = {}
    for p in rsa_logs:
        idx = idx_from_name(p) or len(runs)+1
        runs.setdefault(idx, {})["rsa_log"] = p
    for p in pqc_logs:
        idx = idx_from_name(p) or len(runs)+1
        runs.setdefault(idx, {})["pqc_log"] = p
    for p in rsa_stats:
        idx = idx_from_name(p) or len(runs)+1
        runs.setdefault(idx, {})["rsa_stats"] = p
    for p in pqc_stats:
        idx = idx_from_name(p) or len(runs)+1
        runs.setdefault(idx, {})["pqc_stats"] = p

    resultados = []
    for idx in sorted(runs.keys()):
        resultados.append({"run": idx, **runs[idx]})
    return resultados

def processar_todas_rodadas():
    rodadas = agrupar_por_rodada()
    if not rodadas:
        print("Nenhuma rodada encontrada em:", PASTA_RELATORIOS)
        return None

    dataset = []
    for r in rodadas:
        run_idx = r.get("run")
        item = {"run": run_idx}

        # RSA
        rsa_log = r.get("rsa_log")
        rsa_stats = r.get("rsa_stats")
        if rsa_log and os.path.exists(rsa_log):
            with open(rsa_log, "r", encoding="utf-8") as f:
                conteudo = f.read()
            item["rsa_time_s"] = extrair_numero_tempo(conteudo)
            item["rsa_status"] = extrair_status(conteudo, "rsa")
        else:
            item["rsa_time_s"] = None
            item["rsa_status"] = "N/A"

        if rsa_stats and os.path.exists(rsa_stats):
            parsed = parse_stats_file(rsa_stats)
            if parsed:
                item["rsa_cpu_pct"] = parsed.get("cpu")
                item["rsa_mem_gb"] = parsed.get("mem_gb")
            else:
                item["rsa_cpu_pct"] = None
                item["rsa_mem_gb"] = None
        else:
            item["rsa_cpu_pct"] = None
            item["rsa_mem_gb"] = None

        # PQC
        pqc_log = r.get("pqc_log")
        pqc_stats = r.get("pqc_stats")
        if pqc_log and os.path.exists(pqc_log):
            with open(pqc_log, "r", encoding="utf-8") as f:
                conteudo = f.read()
            item["pqc_time_s"] = extrair_numero_tempo(conteudo)
            item["pqc_status"] = extrair_status(conteudo, "pqc")
        else:
            item["pqc_time_s"] = None
            item["pqc_status"] = "N/A"

        if pqc_stats and os.path.exists(pqc_stats):
            parsed = parse_stats_file(pqc_stats)
            if parsed:
                item["pqc_cpu_pct"] = parsed.get("cpu")
                item["pqc_mem_gb"] = parsed.get("mem_gb")
            else:
                item["pqc_cpu_pct"] = None
                item["pqc_mem_gb"] = None
        else:
            item["pqc_cpu_pct"] = None
            item["pqc_mem_gb"] = None

        dataset.append(item)

    return dataset

def estatisticas_coluna(valores):
    v = [x for x in valores if x is not None]
    if not v:
        return {"count": 0, "mean": None, "stdev": None, "min": None, "max": None}
    if len(v) == 1:
        return {"count": 1, "mean": float(v[0]), "stdev": 0.0, "min": min(v), "max": max(v)}
    return {"count": len(v), "mean": float(mean(v)), "stdev": float(stdev(v)), "min": min(v), "max": max(v)}

def gerar_relatorio_agrupado(dataset):
    rsa_times = [d["rsa_time_s"] for d in dataset]
    pqc_times = [d["pqc_time_s"] for d in dataset]
    rsa_cpu = [d["rsa_cpu_pct"] for d in dataset]
    pqc_cpu = [d["pqc_cpu_pct"] for d in dataset]
    rsa_mem = [d["rsa_mem_gb"] for d in dataset]
    pqc_mem = [d["pqc_mem_gb"] for d in dataset]

    resumo = {
        "rsa_time": estatisticas_coluna(rsa_times),
        "pqc_time": estatisticas_coluna(pqc_times),
        "rsa_cpu": estatisticas_coluna(rsa_cpu),
        "pqc_cpu": estatisticas_coluna(pqc_cpu),
        "rsa_mem_gb": estatisticas_coluna(rsa_mem),
        "pqc_mem_gb": estatisticas_coluna(pqc_mem),
        "runs": len(dataset)
    }
    return resumo

def salvar_resumo_json_csv(resumo, dataset):
    out_json = os.path.join(PASTA_RELATORIOS, "resumo_aggregado.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"summary": resumo, "per_run": dataset}, f, indent=2, ensure_ascii=False)

    csv_path = os.path.join(PASTA_RELATORIOS, "resumo_por_rodada.csv")
    keys = ["run",
            "rsa_time_s", "rsa_status", "rsa_cpu_pct", "rsa_mem_gb",
            "pqc_time_s", "pqc_status", "pqc_cpu_pct", "pqc_mem_gb"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in dataset:
            writer.writerow({k: row.get(k, "") for k in keys})
    print(f"Resumo salvo: {out_json}")
    print(f"CSV por rodada salvo: {csv_path}")

# --- TABELA LIMPA (Apenas médias, sem desvio padrão) ---
def imprimir_tabela_resumo(resumo):
    tabela = [
        ["Métrica", "RSA", "PQC", "Unidade"],
        [
            "CPU",
            f"{resumo['rsa_cpu']['mean']:.2f}" if resumo['rsa_cpu']['mean'] is not None else "N/A",
            f"{resumo['pqc_cpu']['mean']:.2f}" if resumo['pqc_cpu']['mean'] is not None else "N/A",
            "%"
        ],
        [
            "Memória",
            f"{resumo['rsa_mem_gb']['mean']:.2f}" if resumo['rsa_mem_gb']['mean'] is not None else "N/A",
            f"{resumo['pqc_mem_gb']['mean']:.2f}" if resumo['pqc_mem_gb']['mean'] is not None else "N/A",
            "GB"
        ],
        [
            "Tempo",
            f"{resumo['rsa_time']['mean']:.2f}" if resumo['rsa_time']['mean'] is not None else "N/A",
            f"{resumo['pqc_time']['mean']:.2f}" if resumo['pqc_time']['mean'] is not None else "N/A",
            "s"
        ]
    ]
    print("\nResumo agregado:")
    print(tabulate(tabela, headers="firstrow", tablefmt="fancy_grid"))

# --- FUNÇÃO DE GRÁFICO (Sem yerr e com cores corretas e margem) ---
def gerar_graficos_esteticos(resumo, dataset, pasta_saida):
    """
    Gráfico estético usando médias.
    Cores:
      - Iguais: Azul (C0)
      - Diferentes: Menor (Melhor) = Verde, Maior (Pior) = Vermelho
    """
    NUM_RUNS = resumo["runs"]
    labels = ["RSA", "PQC"]

    # Médias
    cpu = [resumo["rsa_cpu"]["mean"] or 0, resumo["pqc_cpu"]["mean"] or 0]
    memoria = [resumo["rsa_mem_gb"]["mean"] or 0, resumo["pqc_mem_gb"]["mean"] or 0]
    tempo = [resumo["rsa_time"]["mean"] or 0, resumo["pqc_time"]["mean"] or 0]
    
    # Cálculo dos valores máximos com margem
    cpu_max_val = max(cpu)
    mem_max_val = max(memoria)
    tempo_max_val = max(tempo)
    
    # Margem segura (25%)
    MARGEM = 1.25 

    # Função interna para definir as cores
    def definir_cores(v1, v2):
        if abs(v1 - v2) < 0.01:
            return ['C0', 'C0'] # Azul padrão
        elif v1 < v2:
            return ['tab:green', 'tab:red'] # Menor é melhor (Verde), Maior é pior (Vermelho)
        else:
            return ['tab:red', 'tab:green'] 

    plt.figure(figsize=(10, 8))
    plt.suptitle(f"Resultados Médios Após {NUM_RUNS} Rodadas de Teste", fontsize=16, fontweight="bold", y=0.98) 

    # 1. CPU
    plt.subplot(3, 1, 1)
    cores_cpu = definir_cores(cpu[0], cpu[1])
    plt.bar(labels, cpu, color=cores_cpu)
    plt.title("CPU (%)") 
    plt.ylabel("CPU (%)")
    plt.ylim(top=cpu_max_val * MARGEM) 
    
    for i, v in enumerate(cpu):
        plt.text(i, v, f"{v:.2f}", ha='center', va='bottom', fontsize=12, fontweight='bold')
    plt.grid(axis='y', linestyle="--", alpha=0.5)

    # 2. Memória
    plt.subplot(3, 1, 2)
    cores_mem = definir_cores(memoria[0], memoria[1])
    plt.bar(labels, memoria, color=cores_mem)
    plt.title("Memória RAM Usada (GB)") 
    plt.ylabel("GB") 
    plt.ylim(top=mem_max_val * MARGEM)
    
    for i, v in enumerate(memoria):
        plt.text(i, v, f"{v:.2f}", ha='center', va='bottom', fontsize=12, fontweight='bold')
    plt.grid(axis='y', linestyle="--", alpha=0.5)

    # 3. Tempo
    plt.subplot(3, 1, 3)
    cores_tempo = definir_cores(tempo[0], tempo[1])
    plt.bar(labels, tempo, color=cores_tempo)
    plt.title("Tempo total (s)") 
    plt.ylabel("Segundos") 
    plt.ylim(top=tempo_max_val * MARGEM)
    
    for i, v in enumerate(tempo):
        plt.text(i, v, f"{v:.1f}s", ha='center', va='bottom', fontsize=12, fontweight='bold')
    plt.grid(axis='y', linestyle="--", alpha=0.5)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 

    caminho_saida = os.path.join(pasta_saida, "grafico_desempenho_estetico.png")
    plt.savefig(caminho_saida, dpi=200)
    plt.show()
    plt.close()
    print(f"\nGráfico gerado com sucesso em:\n{caminho_saida}")

# --- Main CLI ---
def main():
    parser = argparse.ArgumentParser(description="Analisa resultados de múltiplas rodadas RSA/PQC")
    parser.add_argument("--aggregate", action="store_true", help="Agrupa e calcula médias das rodadas encontradas em relatorios/")
    args = parser.parse_args()

    if not os.path.exists(PASTA_RELATORIOS):
        print(f"Pasta de relatórios não encontrada: {PASTA_RELATORIOS}")
        return

    if args.aggregate:
        dataset = processar_todas_rodadas()
        if not dataset:
            print("Nenhum dado de rodadas coletado.")
            return
        resumo = gerar_relatorio_agrupado(dataset)
        salvar_resumo_json_csv(resumo, dataset)
        imprimir_tabela_resumo(resumo)
        gerar_graficos_esteticos(resumo, dataset, PASTA_RELATORIOS)
    else:
        print("Sem argumentos. Use --aggregate para processar as rodadas.")

if __name__ == "__main__":
    main()