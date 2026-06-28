FROM node:22-alpine

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./

EXPOSE 5173
