# Sistema RAG Q&A - Documentación Completa

Sistema completo de Preguntas y Respuestas basado en RAG (Retrieval-Augmented Generation) para documentos PDF institucionales.

## 🚀 Características

- **Gestión de Documentos PDF**: Carga, procesa y gestiona múltiples documentos
- **Vector Database**: Almacenamiento eficiente con Milvus
- **Embeddings**: Generación con Sentence Transformers
- **RAG Pipeline**: Recuperación de contexto + generación con LLM
- **LLM Gratuito**: Integración con Google Gemini 2.5 Flash (GRATIS)
- **API REST**: FastAPI con documentación automática
- **Interfaz Web**: Streamlit intuitiva y responsive
- **Dockerizado**: Deploy completo con Docker Compose

## 📋 Requisitos Previos

- Docker (v20.10+)
- Docker Compose (v2.0+)
- **Google Gemini API Key (GRATIS)** - Obtener en: https://makersuite.google.com/app/apikey
- Mínimo 8GB RAM
- 10GB espacio en disco

## 🔑 Obtener API Key de Gemini (GRATIS)

1. Ve a: **https://makersuite.google.com/app/apikey**
2. Inicia sesión con tu cuenta de Google
3. Haz clic en **"Create API Key"**
4. Copia tu API key (comienza con `AIza...`)
5. ¡Listo! No necesitas tarjeta de crédito

**Límites gratuitos de Gemini:**
- 60 requests por minuto
- Gratis permanentemente
- Sin necesidad de pago

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

Editar `.env` y añadir tu **Gemini API Key**:
```env
# Google Gemini API (GRATIS)
GEMINI_API_KEY=AIzaSy...tu_api_key_aqui

# Configuración del modelo
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
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

**Nota**: La primera construcción puede tardar 10-15 minutos descargando dependencias. Construcciones posteriores serán mucho más rápidas (~2-3 minutos).

### 5. Verificar que Todo Esté Funcionando

Espera aproximadamente 2-3 minutos para que todos los servicios se inicialicen.

**Verificar servicios:**
```bash
# Ver estado de los contenedores
docker compose ps

# Verificar logs del backend
docker compose logs backend | grep "Gemini"

# Deberías ver:
# Gemini client initialized with model: models/gemini-2.5-flash

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
   - Revisar respuesta generada por Gemini y fragmentos recuperados

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
# Hacer pregunta (usando Gemini 2.5 Flash)
curl -X POST "http://localhost:8000/query/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es la política de vacaciones?",
    "top_k": 5
  }'
```

## ⚙️ Configuración Avanzada

### Cambiar Modelo de Gemini

Editar en `.env` o `docker-compose.yml`:
```env
# Modelos disponibles de Gemini:
GEMINI_MODEL=gemini-2.5-flash    # Rápido y eficiente (RECOMENDADO)
GEMINI_MODEL=gemini-2.5-pro      # Mejor calidad, más lento
GEMINI_MODEL=gemini-flash        # Alias para 2.5-flash
```

### Ajustar Parámetros del LLM
```env
LLM_MAX_TOKENS=2048        # Tokens máximos en respuesta
LLM_TEMPERATURE=0.7        # Creatividad (0.0-1.0)
```

### Ajustar Chunking
```env
CHUNK_SIZE=500          # Tamaño de cada fragmento en palabras
CHUNK_OVERLAP=50        # Solapamiento entre fragmentos
```

### Cambiar Modelo de Embeddings
```env
# Opciones disponibles:
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Rápido, 384 dim (ACTUAL)
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # Mejor calidad, 768 dim
```

**Nota**: Si cambias el modelo de embeddings, debes actualizar `MILVUS_DIMENSION` y reindexar todos los documentos.

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

### Problema: Error "insufficient_quota" o problemas con API Key

**Solución**: Verifica que:
1. Tu `GEMINI_API_KEY` esté correctamente configurada en `.env`
2. La API key sea válida (comienza con `AIza...`)
3. No hayas excedido el límite de 60 requests/minuto
```bash
# Verificar que la API key esté cargada
docker compose exec backend printenv | grep GEMINI

# Reiniciar backend con nueva API key
docker compose restart backend
```

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

Opción 1: Reducir batch size en `backend/app/utils/embeddings.py`
```python
embeddings = self.model.encode(texts, batch_size=16)  # Reducir de 32
```

Opción 2: Usar modelo más pequeño
```env
EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L3-v2  # Más rápido
```

### Problema: Gemini responde lento

El modelo `gemini-2.5-flash` es el más rápido. Si aún es lento:

1. Reduce `TOP_K_RESULTS` para enviar menos contexto
2. Reduce `LLM_MAX_TOKENS` para respuestas más cortas
3. Verifica tu conexión a internet
```env
TOP_K_RESULTS=3           # Reducir de 5
LLM_MAX_TOKENS=500        # Reducir de 2048
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

### Estadísticas de uso de Gemini

Puedes monitorear tu uso en: https://makersuite.google.com/app/apikey

## 🔐 Seguridad

### Para Producción

1. **Proteger API Key de Gemini**

Nunca commitear el archivo `.env` al repositorio:
```bash
# Asegúrate de que .env esté en .gitignore
echo ".env" >> .gitignore
```

2. **Cambiar credenciales de MinIO**
```yaml
environment:
  MINIO_ACCESS_KEY: your_secure_key
  MINIO_SECRET_KEY: your_secure_secret
```

3. **Configurar HTTPS**

Usar reverse proxy (Nginx, Traefik) con certificados SSL.

4. **Restringir CORS**

En `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Dominio específico
    ...
)
```

5. **Agregar autenticación**

Implementar JWT tokens o OAuth2 para proteger endpoints.

6. **Limitar uploads**

Ajustar `MAX_FILE_SIZE` y validar tipos de archivo estrictamente.

7. **Rate limiting**

Implementar rate limiting para proteger contra abuso:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

## 📈 Optimizaciones de Rendimiento

### 1. Caché de Embeddings

Implementar Redis para cachear embeddings de queries frecuentes:
```yaml
# Agregar a docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

### 2. Procesamiento Asíncrono

Usar Celery + RabbitMQ para procesar documentos grandes en background.

### 3. Paginación

Implementar paginación en listado de documentos para mejor UX.

### 4. Índices Compuestos en Milvus

Crear índices para campos frecuentemente consultados.

### 5. Compresión de Embeddings

Usar embeddings cuantizados (int8) para reducir tamaño y mejorar velocidad.

## 🧪 Testing

### Test Manual de la API
```bash
# 1. Verificar salud
curl http://localhost:8000/health

# 2. Verificar Gemini
curl http://localhost:8000/query/health

# 3. Subir documento de prueba
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@test.pdf"

# 4. Procesar documento (usar document_id de la respuesta anterior)
curl -X POST "http://localhost:8000/ingest/process" \
  -H "Content-Type: application/json" \
  -d '{"document_id":"abc-123","filename":"test.pdf"}'

# 5. Hacer pregunta
curl -X POST "http://localhost:8000/query/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"¿De qué trata el documento?","top_k":3}'
```

### Test de Frontend

1. Abrir http://localhost:8501
2. Subir un PDF
3. Esperar procesamiento
4. Hacer una pregunta
5. Verificar que la respuesta sea coherente

## 📦 Backup y Restore

### Backup de Datos
```bash
# Crear directorio de backups
mkdir -p backups

# Backup de Milvus
docker run --rm \
  -v rag-qa-system_milvus_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/milvus_backup_$(date +%Y%m%d).tar.gz /data

# Backup de uploads
docker run --rm \
  -v rag-qa-system_backend_uploads:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/uploads_backup_$(date +%Y%m%d).tar.gz /data
```

### Restore de Datos
```bash
# Restore Milvus
docker run --rm \
  -v rag-qa-system_milvus_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu bash -c "rm -rf /data/* && tar xzf /backup/milvus_backup_YYYYMMDD.tar.gz -C /"

# Restore uploads
docker run --rm \
  -v rag-qa-system_backend_uploads:/data \
  -v $(pwd)/backups:/backup \
  ubuntu bash -c "rm -rf /data/* && tar xzf /backup/uploads_backup_YYYYMMDD.tar.gz -C /"

# Reiniciar servicios
docker compose restart
```

## 🌟 Características Destacadas

### ✅ 100% Gratuito
- Usa Google Gemini 2.5 Flash (gratis permanentemente)
- No necesita tarjeta de crédito
- 60 requests/minuto incluidos

### ✅ Alta Calidad
- Modelo Gemini 2.5 Flash es rápido y preciso
- Embeddings con Sentence Transformers
- Vector search con Milvus

### ✅ Fácil de Usar
- Interfaz Streamlit intuitiva
- API REST documentada
- Dockerizado completamente

### ✅ Escalable
- Arquitectura modular
- Fácil de extender
- Production-ready

## 🔄 Cambiar a Otro LLM (Opcional)

Si en el futuro quieres usar otro proveedor:

### Opción 1: OpenAI (Requiere pago)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
```

### Opción 2: Ollama (Local, gratis)

Agrega Ollama a `docker-compose.yml` y cambia:
```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama2
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

- Sistema RAG Q&A - Arquitectura completa

## 🙏 Agradecimientos

- **Google** por Gemini API gratuita
- **Milvus** por la vector database
- **HuggingFace** por Sentence Transformers
- **FastAPI** y **Streamlit** por los frameworks

## 📞 Soporte

- Documentación API: http://localhost:8000/docs
- Issues: GitHub Issues
- Gemini API: https://ai.google.dev/

---

**¿Preguntas frecuentes?**

**P: ¿Gemini es realmente gratis?**
R: Sí, Google ofrece Gemini con un límite generoso de 60 requests/minuto de forma gratuita permanentemente.

**P: ¿Puedo usar mis propios documentos confidenciales?**
R: Sí, pero ten en cuenta que los documentos se envían a la API de Gemini. Para máxima privacidad, considera usar Ollama (LLM local).

**P: ¿Cuántos documentos puedo subir?**
R: No hay límite en el sistema, pero depende de tu espacio en disco y memoria RAM disponible.

**P: ¿Puedo usar esto en producción?**
R: Sí, pero asegúrate de implementar las medidas de seguridad mencionadas en la sección de Seguridad.