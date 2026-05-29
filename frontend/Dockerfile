# Use Node.js alpine runtime for a lightweight image
FROM node:18-alpine

WORKDIR /app

# Copy package configuration files
COPY package.json package-lock.json* ./

# Install npm dependencies
RUN npm ci

# Copy the rest of the application files
COPY . .

# Set up build arguments for client-side environment variables
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the Next.js application
RUN npm run build

# Expose port 3000
EXPOSE 3000

# Start the application in production mode
CMD ["npm", "start"]
