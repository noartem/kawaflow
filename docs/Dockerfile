FROM python:3.12-slim

WORKDIR /app

# Install MkDocs and the Material theme
RUN pip install --no-cache-dir mkdocs mkdocs-material

# Copy documentation files
COPY . .

# Expose port for MkDocs server
EXPOSE 8000

# Command to serve the documentation
CMD ["mkdocs", "serve", "-a", "0.0.0.0:8000"]