FROM python:3.11-slim

# Evita perguntas interativas no apt
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instala dependências de sistema necessárias para o Modeller, compilação e gráficos
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    libgfortran5 \
    libglib2.0-0 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Baixa e instala o Modeller 10.7 com licença acadêmica oficial
ARG MODELLER_KEY="MODELIRANJE"
RUN wget -q https://salilab.org/modeller/10.7/modeller_10.7-1_amd64.deb -O /tmp/modeller.deb && \
    KEY_MODELLER="${MODELLER_KEY}" dpkg -i /tmp/modeller.deb && \
    rm /tmp/modeller.deb

# Configura o PYTHONPATH para carregar o Modeller nativamente
ENV PYTHONPATH="/usr/lib/modeller10.7/modlib:/app:${PYTHONPATH}"

# Define diretório de trabalho
WORKDIR /app

# Instala dependências Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia código do smosh e do projeto Django
COPY smosh /app/smosh
COPY modeller_web /app/modeller_web

# Cria diretórios de media e static se não existirem
RUN mkdir -p /app/modeller_web/media /app/modeller_web/static /app/modeller_web/staticfiles

WORKDIR /app/modeller_web

# Executa migrações e coleta de estáticos
EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
