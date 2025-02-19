FROM php:8.1-apache

# Instalar dependências
RUN apt-get update && apt-get install -y \
    libapache2-mod-php \
    php-sqlite3 \
    git \
    curl \
    unzip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Configurar Apache
COPY . /var/www/html
RUN chown -R www-data:www-data /var/www/html

# Habilitar mod_rewrite
RUN a2enmod rewrite

# Reiniciar Apache
CMD ["apache2-foreground"]