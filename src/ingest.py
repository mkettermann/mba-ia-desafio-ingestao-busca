"""Ingestão do PDF: lê, divide em chunks, gera embeddings e grava no pgVector."""

import sys
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    COLLECTION_NAME,
    INGEST_BATCH_SIZE,
    get_database_url,
    get_embeddings,
    get_pdf_path,
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
MAX_TENTATIVAS = 5
ESPERA_INICIAL = 5


def carregar_chunks(pdf_path):
    """Lê o PDF e devolve os chunks de 1000 caracteres com overlap de 150."""
    paginas = PyPDFLoader(str(pdf_path)).load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=False,
    )
    chunks = splitter.split_documents(paginas)

    # Remove metadados vazios para não poluir o JSONB do banco.
    return [
        Document(
            page_content=chunk.page_content,
            metadata={k: v for k, v in chunk.metadata.items() if v not in ("", None)},
        )
        for chunk in chunks
        if chunk.page_content.strip()
    ]


def _e_limite_de_cota(erro):
    texto = str(erro).upper()
    return "429" in texto or "RESOURCE_EXHAUSTED" in texto or "RATE_LIMIT" in texto


def gravar_lote(store, documentos, ids):
    """Grava um lote, com espera progressiva quando o provedor limita a cota."""
    espera = ESPERA_INICIAL

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            store.add_documents(documents=documentos, ids=ids)
            return
        except Exception as erro:  # noqa: BLE001 - só reagimos a limite de cota
            if tentativa == MAX_TENTATIVAS or not _e_limite_de_cota(erro):
                raise
            print(f"  Limite de cota atingido. Nova tentativa em {espera}s...")
            time.sleep(espera)
            espera *= 2


def ingest_pdf():
    pdf_path = get_pdf_path()
    print(f"Lendo o PDF: {pdf_path}")

    chunks = carregar_chunks(pdf_path)
    if not chunks:
        print("Nenhum conteúdo encontrado no PDF. Nada a ingerir.")
        return

    print(f"{len(chunks)} chunks gerados. Criando embeddings e gravando no banco...")

    store = PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=get_database_url(),
        use_jsonb=True,
    )

    # IDs determinísticos: reexecutar a ingestão atualiza os registros em vez
    # de duplicá-los.
    ids = [f"{pdf_path.stem}-{i}" for i in range(len(chunks))]

    total = len(chunks)
    for inicio in range(0, total, INGEST_BATCH_SIZE):
        fim = min(inicio + INGEST_BATCH_SIZE, total)
        gravar_lote(store, chunks[inicio:fim], ids[inicio:fim])
        print(f"  {fim}/{total} chunks gravados")

    print(f"Ingestão concluída na collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    try:
        ingest_pdf()
    except Exception as erro:  # noqa: BLE001 - erro amigável na CLI
        print(f"Erro durante a ingestão: {erro}", file=sys.stderr)
        sys.exit(1)
