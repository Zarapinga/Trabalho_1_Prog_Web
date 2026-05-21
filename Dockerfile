# Usando uma imagem base oficial e leve do Python
FROM python:3.11-slim

# Configurações para o Python não salvar arquivos .pyc e não reter buffers de saída
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definindo o diretório de trabalho dentro do container
WORKDIR /app

# Instalando dependências do sistema necessárias para compilar o psycopg2 se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiando o arquivo de dependências para o container
COPY requirements.txt /app/

# Instalando as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copiando todo o conteúdo da pasta code para o diretório de trabalho
COPY code/ /app/

# Expõe a porta padrão do servidor de desenvolvimento do Django
EXPOSE 8000

# Comando padrão para rodar as migrações e iniciar o servidor
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]