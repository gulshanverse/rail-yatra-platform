# Build Stage
FROM node:20-alpine AS builder

WORKDIR /usr/src/app

COPY package*.json ./
COPY prisma/ ./prisma/

RUN npm ci

COPY . .

RUN npx prisma generate
RUN npm run build

# Production Stage
FROM node:20-alpine

WORKDIR /usr/src/app

COPY package*.json ./
COPY prisma/ ./prisma/

RUN npm ci --only=production

COPY --from=builder /usr/src/app/dist ./dist
COPY --from=builder /usr/src/app/node_modules/.prisma ./node_modules/.prisma

ENV NODE_ENV=production
ENV PORT=5000

EXPOSE 5000

USER node

CMD ["node", "dist/main"]
