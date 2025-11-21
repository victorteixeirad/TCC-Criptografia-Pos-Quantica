import os
import re
from tabulate import tabulate
import matplotlib.pyplot as plt
import json 

# --- Definições de Caminho ---
# Este script deve estar na pasta 'scripts'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_RELATORIOS = os.path.join(BASE_DIR, "..", "relatorios")
PASTA_RELATORIOS = os.path.normpath(PASTA_RELATORIOS)

# --- Funções de Conversão (Corrigidas para precisão) ---

# Converte unidades Linux (GiB → GB, MiB → MB, KiB → KB, B → KB)
def converter_unidade(valor_str):
    valor_str = valor_str.strip()
    match = re.match(r"([\d\.]+)(GiB|MiB|KiB|B)", valor_str)
    if not match:
        return valor_str
    
    valor, unidade = float(match.group(1)), match.group(2)

    # Fatores de conversão (Binário para Decimal)
    if unidade == "GiB":
        return f"{valor * 1.07374:.2f} GB"
    elif unidade == "MiB":
        return f"{valor * 1.04858:.2f} MB"
    elif unidade == "KiB":
        return f"{valor * 1.024:.2f} KB"
    elif unidade == "B":
        # Converte Bytes para KB para melhor leitura se for um valor grande
        if valor > 1024:
            return f"{valor / 1024:.2f} KB"
        return f"{valor:.0f} B"
    return valor_str


# --- Funções de Parsing Corrigidas ---

def ler_dados_estatisticos(caminho):
    """Lê o arquivo stats e extrai CPU e Memória."""
    dados = {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception:
        return None

    # Regex robusta para ler o formato da tabela docker stats
    # Captura 1: Nome, 2: CPU%, 3: Mem. Usada (MiB/GiB), 4: Limite (GiB), 5: I/O Recebido, 6: I/O Enviado
    match = re.search(r"(\S+)\s+([\d\.]+)\%\s+([\d\.]+MiB|[\d\.]+GiB)\s*/\s*([\d\.]+GiB)\s*([\d\.]+B|[\d\.]+kB)\s*/\s*([\d\.]+B|[\d\.]+kB)", conteudo)

    if match:
        dados["Ambiente"] = match.group(1).replace("_container", "")
        dados["CPU (%)"] = float(match.group(2)) # Mantém como float para o gráfico
        dados["Memória Usada"] = converter_unidade(match.group(3))
        dados["Memória Limite"] = converter_unidade(match.group(4))
        dados["NET I/O (Recebido)"] = converter_unidade(match.group(5))
        dados["NET I/O (Enviado)"] = converter_unidade(match.group(6))
    
    return dados

def ler_dados_log(caminho):
    """Lê o arquivo de log e extrai Tempo e Status."""
    dados = {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception:
        return None

    # Regex para Tempo Total
    tempo = re.search(r"Tempo total de execução.*?(\d+)\s*segundos", conteudo)
    if tempo:
        dados["Tempo Total (s)"] = int(tempo.group(1)) # Mantém como int para o gráfico

    # Define o Status (procura pela linha de conclusão)
    if "rsa_results" in os.path.basename(caminho):
        status = "COMPROMETIDA" if re.search(r"Chave RSA COMPROMETIDA.", conteudo) else "FALHA (Sem Status)"
    else:
        status = "RESISTENTE" if re.search(r"Criptografia PQC demonstrou resistência.", conteudo) else "FALHA (Sem Status)"
    dados["Status Final"] = status
    
    return dados


# --- Função Principal de Consolidação ---

def gerar_relatorio_consolidado():
    dados_finais = []
    
    # 1. Processar RSA
    stats_rsa = ler_dados_estatisticos(os.path.join(PASTA_RELATORIOS, "rsa_stats.txt"))
    log_rsa = ler_dados_log(os.path.join(PASTA_RELATORIOS, "rsa_results.log"))
    
    if stats_rsa and log_rsa:
        dados_finais.append({**stats_rsa, **log_rsa}) # Combina os dicionários
        
    # 2. Processar PQC
    stats_pqc = ler_dados_estatisticos(os.path.join(PASTA_RELATORIOS, "pqc_stats.txt"))
    log_pqc = ler_dados_log(os.path.join(PASTA_RELATORIOS, "pqc_results.log"))
    
    if stats_pqc and log_pqc:
        dados_finais.append({**stats_pqc, **log_pqc})

    return dados_finais

# --- Geração Gráfica ---
def gerar_graficos(dados, pasta_saida):
    """
    Gera gráficos comparativos (CPU, Memória e Tempo) para RSA e PQC.
    """
    # Filtra dados para o gráfico
    nomes = [d["Ambiente"].upper() for d in dados]
    cpu = [d["CPU (%)"] for d in dados]
    tempo = [d["Tempo Total (s)"] for d in dados]
    
    # A memória precisa ser parseada novamente para valor numérico (removendo GB/MB)
    memoria = []
    for d in dados:
        try:
            # Pega o valor numérico da string convertida
            valor = float(re.search(r"([\d\.]+)", d["Memória Usada"]).group(1))
            memoria.append(valor)
        except:
            memoria.append(0)


    # Cria figura
    plt.figure(figsize=(10, 8))
    
    # Subgráfico 1 - CPU
    plt.subplot(3, 1, 1)
    plt.bar(nomes, cpu, color=['darkred', 'darkgreen'])
    plt.title("Uso de CPU (%) - Foco na Carga")
    plt.ylabel("CPU (%)")
    plt.ylim(min(cpu) * 0.9, max(cpu) * 1.1)
    for i, v in enumerate(cpu):
        plt.text(i, v + (max(cpu)*0.01), f"{v:.2f}%", ha='center')
    plt.grid(True, linestyle="--", alpha=0.5)

    # Subgráfico 2 - Memória
    plt.subplot(3, 1, 2)
    plt.bar(nomes, memoria, color="orange")
    plt.title("Memória Usada (GB)")
    plt.ylabel("Memória RAM (GB)")
    for i, v in enumerate(memoria):
        plt.text(i, v + (max(memoria)*0.01), f"{v:.2f}", ha='center')
    plt.grid(True, linestyle="--", alpha=0.5)

    # Subgráfico 3 - Tempo de Execução
    plt.subplot(3, 1, 3)
    plt.bar(nomes, tempo, color="green")
    plt.title("Tempo Total de Execução (s)")
    plt.ylabel("Tempo (s)")
    for i, v in enumerate(tempo):
        plt.text(i, v + 1, f"{v}s\n({dados[i]['Status Final']})", ha='center', fontsize=9)
    plt.grid(True, linestyle="--", alpha=0.5)
    
    plt.tight_layout()

    # Salva o gráfico consolidado
    caminho_saida = os.path.join(pasta_saida, "grafico_desempenho.png")
    plt.savefig(caminho_saida, dpi=200)
    plt.show()
    plt.close()
    
    print(f"\nGráfico gerado com sucesso em:\n{caminho_saida}")


# --- Execução Final ---

if __name__ == "__main__":
    if not os.path.exists(PASTA_RELATORIOS):
        print(f"❌ Pasta de relatórios não encontrada em:\n{PASTA_RELATORIOS}")
        exit()

    relatorios_consolidados = gerar_relatorio_consolidado()
    
    if not relatorios_consolidados or len(relatorios_consolidados) < 2:
        print("⚠️ ERRO: Não foi possível consolidar os dados para ambos os ambientes. Verifique se os 4 arquivos de log foram gerados com dados válidos.")
        exit()

    # --- 1. Geração da Tabela (tabulate) ---
    
    # Garante que as colunas apareçam na ordem correta:
    ordem_colunas = ["Ambiente", "Status Final", "Tempo Total (s)", "CPU (%)", "Memória Usada", "Memória Limite", "NET I/O (Recebido)", "NET I/O (Enviado)"]
    
    # Preenche dados ausentes (para que todas as linhas tenham as mesmas chaves)
    for dado in relatorios_consolidados:
        for chave in ordem_colunas:
            if chave not in dado:
                dado[chave] = 'N/A' 
                
    tabela = tabulate(relatorios_consolidados, headers="keys", tablefmt="fancy_grid")

    # Salva arquivo de saída
    saida_tabela = os.path.join(PASTA_RELATORIOS, "resumo_consolidado_tcc.md")
    with open(saida_tabela, "w", encoding="utf-8") as f:
        f.write(tabela)

    # --- 2. Geração dos Gráficos ---
    gerar_graficos(relatorios_consolidados, PASTA_RELATORIOS)
    
    print(f"\n✅ Relatório consolidado (Tabela) gerado com sucesso em:\n{saida_tabela}")
    print("\n--- Conteúdo do Relatório Consolidado ---")
    print(tabela)