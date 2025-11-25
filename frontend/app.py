import streamlit as st
import requests
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="RAG Q&A System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_healthy' not in st.session_state:
    st.session_state.api_healthy = False

def check_api_health():
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/query/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "healthy"
        return False
    except:
        return False

# Main page
st.title("📚 Sistema RAG de Preguntas y Respuestas")
st.markdown("---")

# Check API health
st.session_state.api_healthy = check_api_health()

if st.session_state.api_healthy:
    st.success("✅ Sistema conectado y funcionando")
else:
    st.error("❌ No se puede conectar con el backend. Verifica que los servicios estén ejecutándose.")
    st.stop()

# Display system info
try:
    response = requests.get(f"{API_BASE_URL}/query/health")
    if response.status_code == 200:
        health_data = response.json()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Estado de Milvus", "Conectado" if health_data.get("milvus_connected") else "Desconectado")
        
        with col2:
            st.metric("Total de Documentos", health_data.get("total_documents", 0))
        
        with col3:
            st.metric("Chunks Totales", health_data.get("total_chunks", 0))
except:
    pass

st.markdown("---")

# Welcome message
st.markdown("""
## Bienvenido al Sistema RAG Q&A

Este sistema te permite:

1. **📤 Subir Documentos PDF** - Carga tus documentos institucionales
2. **💬 Hacer Preguntas** - Consulta información de tus documentos
3. **📋 Gestionar Documentos** - Administra tus documentos indexados

### ¿Cómo empezar?

1. Ve a la página **"📤 Upload Documents"** en la barra lateral
2. Sube uno o más documentos PDF
3. Espera a que se procesen e indexen
4. Ve a **"💬 Ask Questions"** y comienza a preguntar

### Tecnologías

- **FastAPI**: Backend REST API
- **Milvus**: Vector Database
- **Sentence Transformers**: Generación de embeddings
- **OpenAI GPT**: Generación de respuestas
- **Streamlit**: Interfaz de usuario
""")

st.markdown("---")

# Quick stats
st.subheader("📊 Estadísticas Rápidas")

try:
    response = requests.get(f"{API_BASE_URL}/documents/list")
    if response.status_code == 200:
        data = response.json()
        documents = data.get("documents", [])
        
        if documents:
            total_chunks = sum(doc.get("chunk_count", 0) for doc in documents)
            avg_chunks = total_chunks / len(documents) if documents else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Documentos Indexados", len(documents))
            
            with col2:
                st.metric("Total Chunks", total_chunks)
            
            with col3:
                st.metric("Promedio Chunks/Doc", f"{avg_chunks:.1f}")
        else:
            st.info("No hay documentos indexados aún. ¡Comienza subiendo uno!")
except Exception as e:
    st.error(f"Error obteniendo estadísticas: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>RAG Q&A System v1.0.0 | Desarrollado con FastAPI, Streamlit y Milvus</p>
</div>
""", unsafe_allow_html=True)