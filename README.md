# Sistema RAG Q&A - Documentación Completa

Sistema completo de Preguntas y Respuestas basado en RAG (Retrieval-Augmented Generation) para documentos PDF institucionales.

## 🚀 Características

- **Gestión de Documentos PDF**: Carga, procesa y gestiona múltiples documentos
- **Vector Database**: Almacenamiento eficiente con Milvus
- **Embeddings**: Generación con Sentence Transformers
- **RAG Pipeline**: Recuperación de contexto + generación con LLM
- **API REST**: FastAPI con documentación automática
- **Interfaz Web**: Streamlit intuitiva y responsive
- **Dockerizado**: Deploy completo con Docker Compose

## 📋 Requisitos Previos

- Docker (v20.10+)
- Docker Compose (v2.0+)
- OpenAI API Key (para generación de respuestas)
- Mínimo 8GB RAM
- 10GB espacio en disco

## 🛠️ Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd rag-qa-system
```

### 2. Configurar Variables de Entorno
```bash
cp .env.example .env
```

Editar `.env` y añadir tu OpenAI API Key:
```env
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Crear Estructura de Directorios
```bash
mkdir -p backend/uploads
touch backend/uploads/.gitkeep
```

### 4. Construir e Iniciar los Servicios
```bash
# Construir las imágenes
docker compose build

# Iniciar todos los servicios
docker compose up -d

# Ver logs
docker compose logs -f
```

### 5. Verificar que Todo Esté Funcionando

Espera aproximadamente 2-3 minutos para que todos los servicios se inicialicen.

**Verificar servicios:**
```bash
# Ver estado de los contenedores
docker compose ps

# Verificar logs del backend
docker compose logs backend

# Verificar logs de Milvus
docker compose logs milvus-standalone
```

**Acceder a las interfaces:**

- **Frontend Streamlit**: http://localhost:8501
- **Backend API Docs**: http://localhost:8000/docs
- **Milvus Admin**: http://localhost:9091
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## 📖 Uso del Sistema

### Flujo Completo

1. **Subir Documento**
   - Ir a página "📤 Upload Documents"
   - Seleccionar un PDF
   - Hacer clic en "Subir Documento"
   - Esperar procesamiento automático

2. **Hacer Preguntas**
   - Ir a página "💬 Ask Questions"
   - Escribir pregunta en lenguaje natural
   - Revisar respuesta y fragmentos recuperados

3. **Gestionar Documentos**
   - Ir a página "📋 Manage Documents"
   - Ver lista de documentos
   - Eliminar o reindexar según necesario

### Ejemplos de Preguntas
```
- ¿Cuál es la política de vacaciones?
- ¿Qué beneficios ofrece la empresa?
- Explica el proceso de reembolso de gastos
- ¿Cuáles son los requisitos para trabajo remoto?
```

## 🔌 API Endpoints

### Documentos
```bash
# Subir PDF
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@documento.pdf"

# Listar documentos
curl "http://localhost:8000/documents/list"

# Eliminar documento
curl -X DELETE "http://localhost:8000/documents/{document_id}"
```

### Ingesta
```bash
# Procesar documento
curl -X POST "http://localhost:8000/ingest/process" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "abc123",
    "filename": "documento.pdf"
  }'
```

### Consultas
```bash
# Hacer pregunta
curl -X POST "http://localhost:8000/query/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es la política de vacaciones?",
    "top_k": 5
  }'
```

## ⚙️ Configuración Avanzada

### Ajustar Chunking

Editar en `.env` o `docker-compose.yml`:
```env
CHUNK_SIZE=500          # Tamaño de cada fragmento en palabras
CHUNK_OVERLAP=50        # Solapamiento entre fragmentos
```

### Cambiar Modelo de Embeddings
```env
# Opciones disponibles:
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Rápido, 384 dim
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # Mejor calidad, 768 dim
```

**Nota**: Si cambias el modelo, debes actualizar `MILVUS_DIMENSION` y reindexar documentos.

### Usar Modelo LLM Local

Para usar un modelo local en lugar de OpenAI:

1. Modificar `backend/app/utils/llm_client.py`
2. Agregar soporte para Ollama, LlamaCPP, etc.
3. Actualizar `LLM_PROVIDER` en configuración

### Optimizar Milvus

Para mejor rendimiento, ajustar índices en `backend/app/services/vector_service.py`:
```python
index_params = {
    "metric_type": "COSINE",
    "index_type": "IVF_SQ8",  # Más eficiente en memoria
    "params": {"nlist": 256}   # Más clusters = más rápido
}
```

## 🐛 Troubleshooting

### Problema: Milvus no se conecta
```bash
# Verificar estado
docker compose logs milvus-standalone

# Reiniciar servicio
docker compose restart milvus-standalone etcd minio
```

### Problema: Backend no encuentra Milvus
```bash
# Verificar red
docker network inspect rag-qa-system_rag_network

# Verificar conectividad
docker compose exec backend ping milvus-standalone
```

### Problema: Error de memoria

Aumentar recursos de Docker:
- Docker Desktop → Settings → Resources
- Mínimo 8GB RAM, 4 CPUs

### Problema: Embeddings muy lentos

Opción 1: Usar GPU (si disponible)
```env
EMBEDDING_DEVICE=cuda
```

Opción 2: Reducir batch size en código
```python
embeddings = self.model.encode(texts, batch_size=16)  # Reducir de 32
```

### Limpiar Todo y Reiniciar
```bash
# Detener y eliminar contenedores
docker compose down

# Eliminar volúmenes (CUIDADO: borra datos)
docker compose down -v

# Reconstruir
docker compose build --no-cache
docker compose up -d
```

## 📊 Monitoreo y Logs

### Ver logs en tiempo real
```bash
# Todos los servicios
docker compose logs -f

# Solo backend
docker compose logs -f backend

# Solo Milvus
docker compose logs -f milvus-standalone
```

### Verificar salud de servicios
```bash
# Health check de todos los servicios
docker compose ps

# API health endpoint
curl http://localhost:8000/query/health
```

### Estadísticas de Milvus
```bash
# Acceder a Milvus CLI
docker compose exec milvus-standalone milvus-cli

# Ver colecciones
list collections

# Ver estadísticas
show collection -c documents
```

## 🔐 Seguridad

### Para Producción

1. **Cambiar credenciales de MinIO**
```yaml
environment:
  MINIO_ACCESS_KEY: your_secure_key
  MINIO_SECRET_KEY: your_secure_secret
```

2. **Configurar HTTPS**

Usar reverse proxy (Nginx, Traefik) con certificados SSL.

3. **Restringir CORS**

En `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Dominio específico
    ...
)
```

4. **Agregar autenticación**

Implementar JWT tokens o OAuth2.

5. **Limitar uploads**

Ajustar `MAX_FILE_SIZE` y validar tipos de archivo.

## 📈 Optimizaciones de Rendimiento

### 1. Caché de Embeddings

Implementar Redis para cachear embeddings de queries frecuentes.

### 2. Procesamiento Asíncrono

Usar Celery + RabbitMQ para procesar documentos grandes en background.

### 3. Paginación

Implementar paginación en listado de documentos.

### 4. Índices Compuestos

Crear índices en Milvus para campos frecuentemente consultados.

### 5. Compresión

Usar embeddings cuantizados (int8) para reducir tamaño.

## 🧪 Testing

### Ejecutar Tests
```bash
# Backend tests
docker compose exec backend pytest

# Con cobertura
docker compose exec backend pytest --cov=app --cov-report=html
```

### Test Manual de Endpoints

Ver `tests/test_endpoints.sh` para ejemplos de pruebas con curl.

## 📦 Backup y Restore

### Backup de Datos
```bash
# Backup de volúmenes
docker run --rm \
  -v rag-qa-system_milvus_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/milvus_backup.tar.gz /data

# Backup de uploads
docker run --rm \
  -v rag-qa-system_backend_uploads:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/uploads_backup.tar.gz /data
```

### Restore de Datos
```bash
# Restore Milvus
docker run --rm \
  -v rag-qa-system_milvus_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/milvus_backup.tar.gz -C /

# Restore uploads
docker run --rm \
  -v rag-qa-system_backend_uploads:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/uploads_backup.tar.gz -C /
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto está bajo licencia MIT.

## 👥 Autores

- Tu Nombre - Arquitecto Senior

## 🙏 Agradecimientos

- OpenAI por GPT
- Milvus por la vector database
- HuggingFace por Sentence Transformers
- FastAPI y Streamlit por los frameworks
```

### 7.7 backend/uploads/.gitkeep
```
# Este archivo mantiene el directorio en git