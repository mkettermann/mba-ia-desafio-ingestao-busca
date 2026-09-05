# Desafio MBA Engenharia de Software com IA - Full Cycle

Ingestão de um PDF em PostgreSQL + pgVector e um chat de linha de comando que
responde **somente** com base no conteúdo desse PDF.

> **Ambiente de desenvolvimento:** este projeto foi desenvolvido e testado no
> **WSL 2** (Windows Subsystem for Linux 2), com Ubuntu 26.04 LTS e o banco
> rodando em container via Docker Desktop com integração WSL habilitada. Todos
> os comandos deste README são executados no terminal da distro Linux, não no
> PowerShell. Quem ainda não tem o WSL configurado pode seguir o
> [apêndice no fim do arquivo](#apêndice-instalando-o-wsl-2-para-testes).

## Como funciona

| Arquivo | Responsabilidade |
| --- | --- |
| [src/config.py](src/config.py) | Lê o `.env` e cria os objetos de embeddings e LLM (OpenAI ou Gemini) |
| [src/ingest.py](src/ingest.py) | Lê o PDF, divide em chunks de 1000 caracteres com overlap de 150 e grava os vetores no pgVector |
| [src/search.py](src/search.py) | Busca os 10 chunks mais relevantes (`similarity_search_with_score`, `k=10`), monta o prompt e chama a LLM |
| [src/chat.py](src/chat.py) | CLI que recebe as perguntas e imprime as respostas |

## Pré-requisitos

- **WSL 2 com uma distro Linux** (ambiente de referência: Ubuntu 26.04 LTS) —
  ver o [apêndice](#apêndice-instalando-o-wsl-2-para-testes). O projeto também
  roda em Linux nativo ou macOS; o WSL 2 é apenas o ambiente em que foi validado.
- Python 3.11+ (ambiente de referência: Python 3.14)
- Docker e Docker Compose — no WSL 2, via Docker Desktop com a integração da
  distro habilitada
- Uma chave de API da OpenAI **ou** do Google Gemini

## 1. Preparar o ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configurar as variáveis de ambiente

```bash
cp .env.example .env
```

Preencha a chave do provedor escolhido e ajuste `LLM_PROVIDER`:

| Variável | Descrição |
| --- | --- |
| `LLM_PROVIDER` | `google` (padrão) ou `openai` |
| `OPENAI_API_KEY` / `GOOGLE_API_KEY` | Chave do provedor escolhido |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` |
| `OPENAI_LLM_MODEL` | `gpt-5-nano` |
| `GOOGLE_EMBEDDING_MODEL` | `models/gemini-embedding-001` |
| `GOOGLE_LLM_MODEL` | `gemini-3.1-flash-lite` |
| `DATABASE_URL` | Conexão do Postgres (`postgresql+psycopg://postgres:postgres@localhost:5432/rag`) |
| `PG_VECTOR_COLLECTION_NAME` | Nome da collection no pgVector |
| `PDF_PATH` | Caminho do PDF a ser ingerido |
| `SEARCH_K` | Quantidade de chunks recuperados na busca (padrão `10`) |
| `INGEST_BATCH_SIZE` | Chunks enviados por requisição de embeddings (padrão `20`) |

> **Ao trocar de provedor, use outra collection.** Os vetores da OpenAI têm 1536
> dimensões e os do Gemini 3072; misturar os dois na mesma collection causa erro
> de dimensão.

## 3. Subir o banco de dados

```bash
docker compose up -d
```

Sobe o `pgvector/pgvector:pg17` na porta 5432 e cria a extensão `vector`.

## 4. Executar a ingestão do PDF

```bash
python src/ingest.py
```

Saída esperada:

```
Lendo o PDF: /caminho/document.pdf
67 chunks gerados. Criando embeddings e gravando no banco...
  20/67 chunks gravados
  ...
Ingestão concluída na collection 'gemini_collection'.
```

Os IDs dos chunks são determinísticos, então reexecutar a ingestão atualiza os
registros em vez de duplicá-los.

## 5. Rodar o chat

```bash
python src/chat.py
```

```
Faça sua pergunta: Qual o faturamento da Empresa SuperTechIABrazil?

PERGUNTA: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: O faturamento da empresa SuperTechIABrazil é de R$ 10.000.000,00.

---

Faça sua pergunta: Quantos clientes temos em 2024?

PERGUNTA: Quantos clientes temos em 2024?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

Digite `sair` (ou `Ctrl+D`) para encerrar.

## Notas sobre os modelos

- `models/embedding-001` foi descontinuado pelo Google; o substituto é
  `models/gemini-embedding-001`.
- `gemini-2.5-flash-lite` não está mais disponível para contas novas; o projeto
  usa `gemini-3.1-flash-lite`.
- Os modelos da família `gpt-5` aceitam apenas a temperatura padrão, então o
  `temperature=0` só é enviado para os demais modelos.
- No tier gratuito do Gemini, lotes grandes de embeddings estouram a cota. A
  ingestão grava em lotes de `INGEST_BATCH_SIZE` com nova tentativa e espera
  progressiva em caso de erro 429.

## Solução de problemas

**`connection refused` ao conectar no banco:** confirme que o container está de
pé com `docker compose ps`. No WSL 2, a integração do Docker Desktop com a
distro precisa estar ativada — ver o
[apêndice](#3-instalar-o-docker-desktop-e-habilitar-a-integração-com-a-distro).

**`docker: command not found` no WSL 2:** o Docker Desktop está instalado no
Windows, mas a integração com essa distro não foi habilitada. Ative em
*Settings → Resources → WSL Integration* e reabra o terminal.

**Ingestão ou `pip install` muito lentos no WSL 2:** o projeto provavelmente
está em `/mnt/c/...`. Mova o repositório para o sistema de arquivos do Linux
(`~/projetos/...`) e recrie o `.venv`.

---

## Apêndice: instalando o WSL 2 para testes

Esta seção descreve como sair de um Windows "zerado" e chegar ao ambiente em que
o projeto foi desenvolvido. Se você já usa Linux ou macOS, pode ignorá-la.

### Requisitos do Windows

- Windows 10 versão 2004 (build 19041) ou superior, ou Windows 11
- Virtualização habilitada na BIOS/UEFI (Intel VT-x ou AMD-V)

### 1. Instalar o WSL 2

Abra o **PowerShell como Administrador** e execute:

```powershell
wsl --install
```

O comando habilita os recursos necessários do Windows, define o WSL 2 como
versão padrão e instala o Ubuntu. **Reinicie o computador** ao final.

Para escolher outra distro, liste as disponíveis e instale a desejada:

```powershell
wsl --list --online
wsl --install -d Ubuntu-24.04
```

Se o WSL já estiver instalado, garanta que está atualizado e na versão 2:

```powershell
wsl --update
wsl --set-default-version 2
wsl --list --verbose
```

A coluna `VERSION` precisa mostrar `2`. Se alguma distro estiver em `1`,
converta com `wsl --set-version <NomeDaDistro> 2`.

### 2. Criar o usuário Linux

No primeiro boot da distro, o Ubuntu pede um nome de usuário e uma senha. Essa
senha é usada no `sudo` dentro do Linux e não tem relação com a senha do
Windows. Em seguida, atualize os pacotes:

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Instalar o Docker Desktop e habilitar a integração com a distro

1. Baixe e instale o [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/).
2. Em **Settings → General**, mantenha marcado *Use the WSL 2 based engine*.
3. Em **Settings → Resources → WSL Integration**, ative a chave da sua distro
   (ex.: `Ubuntu`) e clique em *Apply & Restart*.

Valide dentro do terminal da distro — o comando precisa responder sem erro:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

Se aparecer `The command 'docker' could not be found in this WSL 2 distro`, a
integração do passo 3 não está ativa para essa distro.

> Alternativa: instalar o Docker Engine direto dentro da distro, sem Docker
> Desktop. Nesse caso, habilite `systemd` criando `/etc/wsl.conf` com o
> conteúdo abaixo e reiniciando o WSL (`wsl --shutdown` no PowerShell), para que
> o serviço do Docker suba junto com a distro.
>
> ```ini
> [boot]
> systemd=true
> ```

### 4. Instalar as dependências de Python na distro

```bash
sudo apt install -y python3 python3-venv python3-pip git
python3 --version
```

### 5. Clonar o projeto **dentro** do sistema de arquivos do Linux

Este passo é importante para o desempenho: trabalhar em `/mnt/c/...` (disco do
Windows visto pelo WSL) deixa o I/O muito mais lento e pode causar problemas de
permissão no `.venv`. Use o `$HOME` do Linux:

```bash
cd ~
mkdir -p projetos && cd projetos
git clone <url-do-repositorio>
cd mba-ia-desafio-ingestao-busca
```

A partir daqui, siga o README desde a seção
[1. Preparar o ambiente Python](#1-preparar-o-ambiente-python).

### Dicas úteis do dia a dia

| Comando | Onde rodar | O que faz |
| --- | --- | --- |
| `wsl` | PowerShell | Abre o terminal da distro padrão |
| `wsl --shutdown` | PowerShell | Desliga o WSL (útil após mudar `/etc/wsl.conf`) |
| `wsl --list --verbose` | PowerShell | Lista as distros, o estado e a versão do WSL |
| `code .` | WSL | Abre o VS Code no Windows conectado à distro (extensão *WSL*) |
| `explorer.exe .` | WSL | Abre a pasta atual do Linux no Explorer do Windows |

O `localhost` é compartilhado entre Windows e WSL 2, então o Postgres exposto na
porta 5432 pelo `docker compose` fica acessível como `localhost:5432` nos dois
lados — que é exatamente o valor usado em `DATABASE_URL`.
