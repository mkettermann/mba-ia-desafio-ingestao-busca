# Desafio MBA Engenharia de Software com IA - Full Cycle

Ingestão de um PDF em PostgreSQL + pgVector e um chat de linha de comando que
responde **somente** com base no conteúdo desse PDF.

## Como funciona

| Arquivo | Responsabilidade |
| --- | --- |
| [src/config.py](src/config.py) | Lê o `.env` e cria os objetos de embeddings e LLM (OpenAI ou Gemini) |
| [src/ingest.py](src/ingest.py) | Lê o PDF, divide em chunks de 1000 caracteres com overlap de 150 e grava os vetores no pgVector |
| [src/search.py](src/search.py) | Busca os 10 chunks mais relevantes (`similarity_search_with_score`, `k=10`), monta o prompt e chama a LLM |
| [src/chat.py](src/chat.py) | CLI que recebe as perguntas e imprime as respostas |

## Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
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
distro precisa estar ativada.
