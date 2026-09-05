"""Configuração compartilhada entre a ingestão e a busca.

Centraliza a leitura do .env e a criação dos objetos de embeddings e LLM,
que podem ser da OpenAI ou do Google Gemini conforme a variável LLM_PROVIDER.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()
DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME", "documents")
SEARCH_K = int(os.getenv("SEARCH_K", "10"))

# Lotes pequenos evitam estourar o limite de requisições dos provedores.
INGEST_BATCH_SIZE = int(os.getenv("INGEST_BATCH_SIZE", "20"))

# Evita que avisos informativos do SDK do Gemini poluam a saída da CLI.
logging.getLogger("google_genai.models").setLevel(logging.ERROR)


def _obrigatorio(nome):
    valor = os.getenv(nome)
    if not valor:
        raise RuntimeError(
            f"A variável de ambiente {nome} não está definida. "
            f"Copie o .env.example para .env e preencha os valores."
        )
    return valor


def get_pdf_path():
    """Caminho absoluto do PDF configurado em PDF_PATH."""
    caminho = Path(_obrigatorio("PDF_PATH")).expanduser()
    if not caminho.is_absolute():
        caminho = BASE_DIR / caminho
    if not caminho.is_file():
        raise FileNotFoundError(f"PDF não encontrado em: {caminho}")
    return caminho


def get_database_url():
    if not DATABASE_URL:
        raise RuntimeError(
            "A variável de ambiente DATABASE_URL não está definida. "
            "Exemplo: postgresql+psycopg://postgres:postgres@localhost:5432/rag"
        )
    return DATABASE_URL


def get_embeddings():
    """Modelo de embeddings do provedor configurado."""
    if PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings

        _obrigatorio("OPENAI_API_KEY")
        return OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )

    if PROVIDER in ("google", "gemini"):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        _obrigatorio("GOOGLE_API_KEY")
        return GoogleGenerativeAIEmbeddings(
            model=os.getenv("GOOGLE_EMBEDDING_MODEL", "models/gemini-embedding-001")
        )

    raise RuntimeError(
        f"LLM_PROVIDER inválido: '{PROVIDER}'. Use 'openai' ou 'google'."
    )


def get_llm():
    """LLM que responde as perguntas, sempre determinístico (temperature=0)."""
    if PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        _obrigatorio("OPENAI_API_KEY")
        modelo = os.getenv("OPENAI_LLM_MODEL", "gpt-5-nano")
        # Os modelos da família gpt-5 aceitam apenas a temperatura padrão.
        extras = {} if modelo.startswith("gpt-5") else {"temperature": 0}
        return ChatOpenAI(model=modelo, **extras)

    if PROVIDER in ("google", "gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        _obrigatorio("GOOGLE_API_KEY")
        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_LLM_MODEL", "gemini-3.1-flash-lite"),
            temperature=0,
        )

    raise RuntimeError(
        f"LLM_PROVIDER inválido: '{PROVIDER}'. Use 'openai' ou 'google'."
    )
