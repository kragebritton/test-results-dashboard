# Multi-stage build to assemble the frontend and backend into a single image
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Install frontend dependencies and build the production assets
COPY frontend/package.json ./
RUN npm install
COPY frontend .
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install backend dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir fastapi==0.110.3 uvicorn[standard]==0.29.0 \
    python-multipart==0.0.9 pydantic==2.7.1

# Copy backend source
COPY backend ./backend

# Copy built frontend assets into the backend directory
COPY --from=frontend-builder /app/frontend/dist ./backend/static

EXPOSE 8000
WORKDIR /app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
