# frontend/Dockerfile
FROM node:18.12.1

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

CMD ["npm", "start"]
