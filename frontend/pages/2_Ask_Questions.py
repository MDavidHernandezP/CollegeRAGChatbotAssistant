import streamlit as st
import requests
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Ask Questions",
    page_icon="💬",
    layout="wide"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")

st.title("💬 Preguntas y Respuestas")
st.markdown("---")

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Check if there are documents
@st.cache_data(ttl=10)
def get_document_count():
    try:
        response = requests.get(f"{API_BASE_URL}/documents/list")
        if response.status_code == 200:
            data = response.json()
            return data.get("total_count", 0)
    except:
        return 0
    return 0

doc_count = get_document_count()

if doc_count == 0:
    st.warning("⚠️ No hay documentos indexados en el sistema.")
    st.info("👉 Ve a la página 'Upload Documents' para subir y procesar documentos primero.")
    st.stop()

# Sidebar - Query settings
with st.sidebar:
    st.header("⚙️ Configuración de Búsqueda")
    
    top_k = st.slider(
        "Número de fragmentos a recuperar",
        min_value=1,
        max_value=10,
        value=5,
        help="Cuántos fragmentos relevantes se usarán para generar la respuesta"
    )
    
    st.markdown("---")
    
    show_chunks = st.checkbox(
        "Mostrar fragmentos recuperados",
        value=True,
        help="Muestra los fragmentos de texto usados para generar la respuesta"
    )
    
    show_metadata = st.checkbox(
        "Mostrar metadatos",
        value=True,
        help="Muestra información sobre la fuente de cada fragmento"
    )
    
    st.markdown("---")
    
    st.subheader("📊 Estadísticas")
    st.metric("Documentos disponibles", doc_count)
    st.metric("Preguntas en esta sesión", len(st.session_state.chat_history))
    
    if st.button("🗑️ Limpiar Historial"):
        st.session_state.chat_history = []
        st.rerun()

# Main content
st.subheader("🤔 Haz una Pregunta")

# Question input
question = st.text_area(
    "Escribe tu pregunta aquí:",
    placeholder="Ejemplo: ¿Cuál es la política de vacaciones de la empresa?",
    height=100,
    help="Escribe una pregunta específica sobre el contenido de tus documentos"
)

# Example questions
with st.expander("💡 Ver ejemplos de preguntas"):
    st.markdown("""
    **Ejemplos de buenas preguntas:**
    
    - ¿Cuál es el proceso para solicitar vacaciones?
    - ¿Qué beneficios ofrece la empresa a los empleados?
    - ¿Cuáles son los requisitos para el reembolso de gastos?
    - Explica la política de trabajo remoto
    - ¿Qué documentos se necesitan para el onboarding?
    
    **Tips para mejores resultados:**
    
    ✅ Sé específico en tu pregunta
    ✅ Usa términos que probablemente aparezcan en los documentos
    ✅ Pregunta una cosa a la vez
    ❌ Evita preguntas muy generales o ambiguas
    """)

col1, col2 = st.columns([3, 1])

with col1:
    ask_button = st.button("🔍 Buscar Respuesta", type="primary", use_container_width=True)

with col2:
    search_only = st.checkbox("Solo búsqueda", help="Realizar búsqueda semántica sin generar respuesta")

# Process question
if ask_button and question.strip():
    with st.spinner("🤔 Analizando tu pregunta y buscando información..."):
        try:
            if search_only:
                # Semantic search only
                response = requests.post(
                    f"{API_BASE_URL}/query/search",
                    json={
                        "question": question,
                        "top_k": top_k
                    },
                    timeout=60
                )
            else:
                # Full RAG query
                response = requests.post(
                    f"{API_BASE_URL}/query/ask",
                    json={
                        "question": question,
                        "top_k": top_k
                    },
                    timeout=120
                )
            
            if response.status_code == 200:
                data = response.json()
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "question": question,
                    "data": data,
                    "timestamp": datetime.now(),
                    "search_only": search_only
                })
                
                # Display result
                st.markdown("---")
                st.success("✅ Respuesta generada exitosamente")
                
                if not search_only:
                    # Show answer
                    st.subheader("📝 Respuesta")
                    st.markdown(f"**Pregunta:** {question}")
                    st.markdown("**Respuesta:**")
                    st.info(data["answer"])
                    
                    # Show processing time
                    processing_time = data.get("processing_time", 0)
                    st.caption(f"⏱️ Tiempo de procesamiento: {processing_time:.2f} segundos")
                
                # Show retrieved chunks
                if show_chunks:
                    st.markdown("---")
                    st.subheader("📚 Fragmentos Relevantes Encontrados")
                    
                    if search_only:
                        chunks = data.get("results", [])
                    else:
                        chunks = data.get("retrieved_chunks", [])
                    
                    if chunks:
                        for idx, chunk in enumerate(chunks, 1):
                            with st.expander(f"📄 Fragmento {idx} (Relevancia: {chunk.get('score', 0):.4f})"):
                                st.markdown(chunk.get("text", ""))
                                
                                if show_metadata:
                                    st.markdown("---")
                                    metadata = chunk.get("metadata", {})
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.caption(f"📁 **Archivo:** {metadata.get('filename', 'N/A')}")
                                    
                                    with col2:
                                        st.caption(f"📄 **Página:** {metadata.get('page_number', 'N/A')}")
                                    
                                    with col3:
                                        st.caption(f"🔢 **Chunk:** {metadata.get('chunk_index', 'N/A')}")
                    else:
                        st.warning("No se encontraron fragmentos relevantes para tu pregunta.")
            
            else:
                error_detail = response.json().get("detail", "Error desconocido")
                st.error(f"❌ Error: {error_detail}")
        
        except requests.exceptions.Timeout:
            st.error("⏱️ Timeout - La consulta tardó demasiado. Intenta con una pregunta más específica.")
        except Exception as e:
            st.error(f"❌ Error procesando pregunta: {str(e)}")

elif ask_button:
    st.warning("⚠️ Por favor escribe una pregunta antes de buscar.")

# Display chat history
if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("📜 Historial de Consultas")
    
    for idx, entry in enumerate(reversed(st.session_state.chat_history[-5:])):
        with st.expander(
            f"{'🔍' if entry['search_only'] else '💬'} {entry['question'][:80]}... - {entry['timestamp'].strftime('%H:%M:%S')}"
        ):
            st.markdown(f"**Pregunta:** {entry['question']}")
            
            if not entry['search_only']:
                st.markdown("**Respuesta:**")
                st.info(entry['data'].get('answer', 'N/A'))
            
            chunks_count = len(entry['data'].get('retrieved_chunks', []) or entry['data'].get('results', []))
            st.caption(f"📚 {chunks_count} fragmentos recuperados")

# Instructions
st.markdown("---")
with st.expander("📖 Cómo usar esta página"):
    st.markdown("""
    ### Pasos para hacer preguntas:
    
    1. **Escribe tu pregunta** en el área de texto
    2. **Ajusta la configuración** en la barra lateral (opcional)
    3. **Haz clic en "Buscar Respuesta"**
    4. **Revisa la respuesta** y los fragmentos relevantes
    5. **Refina tu pregunta** si es necesario para obtener mejores resultados
    
    ### Configuración disponible:
    
    - **Número de fragmentos**: Cuántos fragmentos del documento se usarán como contexto
    - **Mostrar fragmentos**: Ver los textos originales usados para la respuesta
    - **Mostrar metadatos**: Ver información sobre la fuente de cada fragmento
    - **Solo búsqueda**: Realizar búsqueda sin generar respuesta (más rápido)
    
    ### Tips:
    
    - Preguntas más específicas generan mejores respuestas
    - Revisa los fragmentos recuperados para entender de dónde viene la información
    - Usa el historial para comparar diferentes formulaciones de preguntas
    """)