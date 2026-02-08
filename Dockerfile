# Build the React UI
FROM node:20-alpine AS ui-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
ARG VITE_DISABLE_GRPC=1
ENV VITE_DISABLE_GRPC=${VITE_DISABLE_GRPC}
RUN npm run build

# Run the Python API + serve static UI
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app.py core.py telemetry.py bench.py ./
COPY grpc_backend ./grpc_backend
COPY --from=ui-build /app/frontend/dist ./frontend/dist

EXPOSE 7860
CMD ["python", "app.py"]
