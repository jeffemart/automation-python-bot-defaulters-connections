# Use a imagem oficial do Python como base
FROM python:3.12-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie o arquivo Poetry.lock e pyproject.toml para o diretório de trabalho
COPY pyproject.toml poetry.lock /app/

# Instale o Poetry
RUN pip install --no-cache-dir poetry

# Instala as dependências
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copie o restante dos arquivos do projeto para o diretório de trabalho
COPY . /app/

# Defina a variável de ambiente para não criar o ambiente virtual
ENV POETRY_VIRTUALENVS_CREATE=false

# Comando para rodar o projeto
CMD ["python", "main.py"]