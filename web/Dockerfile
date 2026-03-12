FROM node:22-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 复制生产环境配置文件
# Next.js 会根据 NODE_ENV=production 自动加载 .env.production
COPY .env.production .env.production

# 设置生产环境，Next.js 会自动加载 .env.production
ENV NODE_ENV=production

RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    PORT=3000

# 复制构建产物与依赖（Next.js standalone）
COPY --from=builder /app/.next/standalone ./standalone
COPY --from=builder /app/.next/static ./standalone/.next/static
COPY --from=builder /app/public ./standalone/public

# 复制生产环境配置文件到 standalone 目录
# Next.js 在运行时需要读取环境变量
COPY --from=builder /app/.env.production ./standalone/.env.production

WORKDIR /app/standalone
EXPOSE 3000

CMD ["node", "server.js"]

