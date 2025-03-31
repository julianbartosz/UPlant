# frontend/Dockerfile

FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Use Alpine and avoid architecture-specific modules completely
RUN apk add --no-cache python3 make g++ && \
    npm install --no-optional --no-package-lock --force && \
    npm install esbuild@0.17.19 --no-package-lock --force

# Disable Rollup native optimization flag
ENV ROLLUP_SKIP_OPTIMIZE=true

# Copy the rest of the app
COPY . .

EXPOSE 5137

# Use a simpler server since Vite is having issues
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]