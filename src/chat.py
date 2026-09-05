"""CLI de perguntas e respostas sobre o conteúdo do PDF ingerido."""

import sys

from search import search_prompt

COMANDOS_DE_SAIDA = {"sair", "exit", "quit"}


def main():
    try:
        chain = search_prompt()
    except Exception as erro:  # noqa: BLE001 - erro amigável na CLI
        print(f"Erro de inicialização: {erro}", file=sys.stderr)
        chain = None

    if not chain:
        print("Não foi possível iniciar o chat. Verifique os erros de inicialização.")
        return

    print("Chat iniciado. Digite 'sair' para encerrar.\n")

    while True:
        try:
            pergunta = input("Faça sua pergunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            return

        if not pergunta:
            continue

        if pergunta.lower() in COMANDOS_DE_SAIDA:
            print("Até logo!")
            return

        try:
            resposta = chain.invoke(pergunta).strip()
        except Exception as erro:  # noqa: BLE001 - não derruba o chat
            print(f"Erro ao responder: {erro}\n", file=sys.stderr)
            continue

        print(f"\nPERGUNTA: {pergunta}")
        print(f"RESPOSTA: {resposta}\n")
        print("---\n")


if __name__ == "__main__":
    main()
