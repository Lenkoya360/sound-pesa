# Sound Pesa Mobile App Dockerfile
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Install dependencies for building
RUN apk add --no-cache libc6-compat

# Install Expo CLI globally
RUN npm install -g @expo/cli

# Development stage
FROM base as development

# Copy root package files for workspace
COPY package*.json ./

# Copy package files for workspace structure
COPY packages/app/package*.json ./packages/app/
COPY packages/shared/package*.json ./packages/shared/

# Install dependencies using workspace
RUN npm ci

# Copy source code
COPY packages/app ./packages/app
COPY packages/shared ./packages/shared

# Build shared package
RUN cd packages/shared && npm run build

# Set working directory to app package
WORKDIR /app/packages/app

# Expose ports for Expo development server
EXPOSE 8081 19000 19001 19002

# Development command
CMD ["npx", "expo", "start", "--dev-client"]

# Production build stage (for building the app)
FROM base as builder

# Copy root package files for workspace
COPY package*.json ./

# Copy package files for workspace structure
COPY packages/app/package*.json ./packages/app/
COPY packages/shared/package*.json ./packages/shared/

# Install dependencies using workspace
RUN npm ci

# Copy source code
COPY packages/app ./packages/app
COPY packages/shared ./packages/shared

# Build shared package
RUN cd packages/shared && npm run build

# Set working directory to app package
WORKDIR /app/packages/app

# Build the app (this would be used for creating production builds)
RUN npx expo export --platform all

# Production stage (for serving built app or running in production mode)
FROM base as production

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S expo -u 1001

# Set working directory
WORKDIR /app

# Copy built application
COPY --from=builder --chown=expo:nodejs /app/packages/app/dist ./dist
COPY --from=builder --chown=expo:nodejs /app/packages/app/package*.json ./

# Install only production dependencies
RUN npm ci --only=production

# Switch to non-root user
USER expo

# Expose port
EXPOSE 8081

# Production command (serve the built app)
CMD ["npx", "serve", "dist", "-p", "8081"]