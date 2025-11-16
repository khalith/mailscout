# ============================
# Builder
# ============================
FROM node:18 AS builder

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install

# Copy rest of app
COPY . .

# Build
RUN npm run build


# ============================
# Nginx Runtime
# ============================
FROM nginx:1.25

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 5173
