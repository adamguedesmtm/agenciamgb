FROM php:7.4-apache

# Install dependencies
RUN docker-php-ext-install pdo pdo_mysql

# Copy application code
COPY . /var/www/html/

# Set working directory
WORKDIR /var/www/html/

# Expose port
EXPOSE 80