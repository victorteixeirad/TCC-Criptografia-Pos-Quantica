# Pré-requisitos
Para executar as simulações, é necessário ter o Docker Engine instalado em seu sistema.
Após a instalação, certifique-se de que o Docker esteja em execução em segundo plano. O próprio software ajusta automaticamente as configurações mais adequadas para o ambiente.

# Tipos de Execução

O projeto oferece dois modos principais de execução:
* Criação das imagens dos ambientes clássico e pós-quântico
Ambos os ambientes utilizam bibliotecas validadas para testes controlados de criptografia (RSA e PQC – Dilithium2).
* Simulação e análise de desempenho
Os resultados gerados são armazenados automaticamente na pasta relatórios, seguindo o padrão de unidades utilizado nos containers Docker (Linux).

# Criar imagens e rodar a simulação
*OBS: Para executar ambos os scripts, certifique-se de que esteja na pasta "scritp" dentro do terminal.*

./run_simulation.sh 

Este comando irá:
* Criar as imagens dos ambientes RSA e PQC (Dilithium2)
* Executar as simulações de ambos
* Gerar os relatórios automaticamente

# Converter e analisar os resultados
./analyze_performance.py

Este script realiza:
* Conversão automática das métricas para os padrões decimais (GB, MB, KB)
* Geração de um gráfico comparativo de desempenho para facilitar a visualização dos resultados
