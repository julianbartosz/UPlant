# frontend/Dockerfile
# Use an official Node.js runtime as a parent image
FROM node:18

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json files
COPY package*.json ./

# Install any needed packages
RUN npm ci --no-optional

# Explicitly install the missing module for ARM64
RUN npm install @rollup/rollup-linux-arm64-gnu

# Copy the current directory contents into the container at /app
COPY . .

# Build the app
RUN npm run build

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Run the application
CMD ["npm", "run", "dev"]