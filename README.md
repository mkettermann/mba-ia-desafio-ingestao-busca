# Desafio MBA Engenharia de Software com IA - Full Cycle

Descreva abaixo como executar a sua solução.

# 1. Criar o venv (vai criar uma pasta .venv dentro do projeto)
python3 -m venv .venv

# 2. Ativar o venv
source .venv/bin/activate

# 3. Confirmar que ativou (deve aparecer (.venv) no prompt)
which python

# 4. Atualizar o pip (opcional, mas recomendado)
pip install --upgrade pip

# 5. Instalar as dependências
pip install -r requirements.txt

# 6. Instalar as demais
pip install langchain langchain-openai langchain-google-genai langchain-community langchain-text-splitters langchain-postgres psycopg[binary] python-dotenv beautifulsoup4 pypdf && pip freeze > requirements.txt
