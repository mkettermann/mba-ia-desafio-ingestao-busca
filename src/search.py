"""Busca semântica no pgVector + montagem do prompt enviado à LLM."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_postgres import PGVector

from config import (
    COLLECTION_NAME,
    SEARCH_K,
    get_database_url,
    get_embeddings,
    get_llm,
)

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def get_vector_store():
    """Conexão com a collection do pgVector usada na ingestão."""
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=get_database_url(),
        use_jsonb=True,
    )


def build_chain():
    """Chain que recebe a pergunta (string) e devolve a resposta (string)."""
    store = get_vector_store()

    def buscar_contexto(pergunta):
        # 1. Vetoriza a pergunta e 2. busca os k resultados mais relevantes.
        resultados = store.similarity_search_with_score(pergunta, k=SEARCH_K)
        return "\n\n---\n\n".join(documento.page_content for documento, _ in resultados)

    # 3. Monta o prompt e chama a LLM.
    return (
        RunnableParallel(
            contexto=RunnableLambda(buscar_contexto),
            pergunta=RunnablePassthrough(),
        )
        | PromptTemplate.from_template(PROMPT_TEMPLATE)
        | get_llm()
        | StrOutputParser()
    )


def search_prompt(question=None):
    """Sem argumento devolve a chain pronta; com a pergunta devolve a resposta."""
    chain = build_chain()

    if question is None:
        return chain

    return chain.invoke(question).strip()
