# ReRun Frontend Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production server stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx configuration for SPA routing and proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
