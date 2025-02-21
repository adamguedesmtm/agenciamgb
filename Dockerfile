FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos necessários
COPY requirements.txt .
COPY src/ .
COPY .env .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Criar diretórios necessários
RUN mkdir -p /opt/cs2server/assets/fonts \
    && mkdir -p /opt/cs2server/assets/templates \
    && mkdir -p /opt/cs2server/assets/ranks \
    && mkdir -p /var/log/cs2server \
    && mkdir -p /tmp/map_images \
    && mkdir -p /tmp/player_cards

# Comando para executar o bot
CMD ["python", "bot/main.py"]