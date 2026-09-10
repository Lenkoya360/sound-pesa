# Sound Pesa Web Application Dockerfile
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Install dependencies for building
RUN apk add --no-cache libc6-compat

# Development stage
FROM base as development

# Copy root package files for workspace
COPY package*.json ./

# Copy package files for workspace structure
COPY packages/web/package*.json ./packages/web/
COPY packages/shared/package*.json ./packages/shared/

# Install dependencies using workspace
RUN npm ci

# Copy source code
COPY packages/web ./packages/web
COPY packages/shared ./packages/shared

# Build shared package
RUN cd packages/shared && npm run build

# Set working directory to web package
WORKDIR /app/packages/web

# Expose port
EXPOSE 3000

# Development command with hot reload
CMD ["npm", "run", "dev"]

# Production build stage
FROM base as builder

# Copy root package files for workspace
COPY package*.json ./

# Copy package files for workspace structure
COPY packages/web/package*.json ./packages/web/
COPY packages/shared/package*.json ./packages/shared/

# Install dependencies using workspace
RUN npm ci

# Copy source code
COPY packages/web ./packages/web
COPY packages/shared ./packages/shared

# Build shared package
RUN cd packages/shared && npm run build

# Build web application
WORKDIR /app/packages/web
RUN npm run build

# Production stage
FROM node:18-alpine as production

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Set working directory
WORKDIR /app

# Copy built application
COPY --from=builder /app/packages/web/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/packages/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/packages/web/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

# Production command
CMD ["node", "server.js"]