# QuantDinger Frontend Dockerfile
# Stage 1: Build stage
# 使用阿里云Node.js镜像源
FROM node:18-alpine as builder

WORKDIR /app

# 配置npm使用淘宝镜像源
RUN npm config set registry https://registry.npmmirror.com

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml* ./
COPY yarn.lock* ./

# Install dependencies (prefer npm)
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build production version
RUN npm run build

# Stage 2: Production image (using nginx)
FROM nginx:alpine

# Copy build artifacts
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY deploy/nginx-docker.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
