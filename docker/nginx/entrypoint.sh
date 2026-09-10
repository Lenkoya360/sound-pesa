#!/bin/bash
set -e

# Generate DH parameters if they don't exist
if [ ! -f /etc/nginx/ssl/dhparam.pem ]; then
    echo "Generating DH parameters..."
    openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048
fi

# Check if SSL certificates exist
if [ ! -f /etc/letsencrypt/live/domain/fullchain.pem ]; then
    echo "SSL certificates not found. Using self-signed certificates for initial setup..."
    
    # Create self-signed certificate for initial setup
    mkdir -p /etc/nginx/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/nginx-selfsigned.key \
        -out /etc/nginx/ssl/nginx-selfsigned.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    # Update nginx configuration to use self-signed certificates
    sed -i 's|/etc/letsencrypt/live/domain/fullchain.pem|/etc/nginx/ssl/nginx-selfsigned.crt|g' /etc/nginx/conf.d/default.conf
    sed -i 's|/etc/letsencrypt/live/domain/privkey.pem|/etc/nginx/ssl/nginx-selfsigned.key|g' /etc/nginx/conf.d/default.conf
fi

# Test nginx configuration
nginx -t

# Start nginx
exec "$@"