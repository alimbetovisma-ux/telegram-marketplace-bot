FROM node:20-alpine AS webapp-build
WORKDIR /webapp
COPY webapp/package.json ./
RUN npm install
COPY webapp/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONPATH=/srv

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=webapp-build /webapp/dist ./webapp/dist

EXPOSE 8000
