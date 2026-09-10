# Sound Pesa Nginx Dockerfile
FROM nginx:alpine as base

# Install additional tools
RUN apk add --no-cache curl

# Development stage
FROM base as development

# Copy development nginx configuration
COPY docker/nginx/nginx.dev.conf /etc/nginx/nginx.conf
COPY docker/nginx/default.dev.conf /etc/nginx/conf.d/default.conf

# Create necessary directories
RUN mkdir -p /var/log/nginx /var/cache/nginx

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Production stage
FROM base as production

# Copy production nginx configuration
COPY docker/nginx/nginx.prod.conf /etc/nginx/nginx.conf
COPY docker/nginx/default.prod.conf /etc/nginx/conf.d/default.conf

# Copy SSL configuration template
COPY docker/nginx/ssl.conf /etc/nginx/conf.d/ssl.conf.template

# Create necessary directories
RUN mkdir -p /var/log/nginx /var/cache/nginx /etc/nginx/ssl

# Create non-root user for nginx worker processes
RUN adduser -D -s /bin/false nginx || true

# Set proper permissions
RUN chown -R nginx:nginx /var/cache/nginx /var/log/nginx

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]