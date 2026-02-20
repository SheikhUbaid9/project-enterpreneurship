FROM node:20-alpine
WORKDIR /app


COPY . .
RUN npm install
RUN npm run build -w shared && npm run build -w worker

CMD ["npm", "run", "start", "-w", "worker"]