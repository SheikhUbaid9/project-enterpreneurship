FROM node:20-alpine
WORKDIR /app


COPY . .
RUN npm install
RUN npm run build -w shared && npm run build -w api

EXPOSE 3000
CMD ["npm", "run", "start", "-w", "api"]