import streamlit as st
import requests
import os
from datetime import datetime
import pandas as pd

# Page config
st.set_page_config(
    page_title="Manage Documents",
    page_icon="📋",
    layout="wide"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")

st.title("📋 Gestión de Documentos")
st.markdown("---")

# Function to get documents
@st.cache_data(ttl=5)
def get_documents():
    try:
        response = requests.get(f"{API_BASE_URL}/documents/list")
        if response.status_code == 200:
            data = response.json()
            return data.get("documents", [])
    except Exception as e:
        st.error(f"Error obteniendo documentos: {str(e)}")
    return []

# Function to delete document
def delete_document(document_id, filename):
    try:
        response = requests.delete(f"{API_BASE_URL}/documents/{document_id}")
        if response.status_code == 200:
            st.success(f"✅ Documento '{filename}' eliminado exitosamente")
            st.cache_data.clear()
            return True
        else:
            st.error(f"❌ Error eliminando documento: {response.text}")
            return False
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False

# Function to reindex document
def reindex_document(document_id, filename):
    try:
        with st.spinner(f"Reindexando '{filename}'..."):
            response = requests.post(f"{API_BASE_URL}/ingest/reindex/{document_id}")
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ Documento reindexado exitosamente")
                st.info(f"Chunks antiguos eliminados: {data.get('old_chunks_deleted', 0)}")
                st.info(f"Chunks nuevos creados: {data.get('new_chunks_created', 0)}")
                st.cache_data.clear()
                return True
            else:
                st.error(f"❌ Error reindexando: {response.text}")
                return False
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False

# Refresh button
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Get documents
documents = get_documents()

if not documents:
    st.info("📭 No hay documentos en el sistema.")
    st.markdown("""
    ### ¿Qué hacer ahora?
    
    👉 Ve a la página **"📤 Upload Documents"** para subir tus primeros documentos.
    """)
    st.stop()

# Display statistics
st.subheader("📊 Estadísticas Generales")

total_docs = len(documents)
total_chunks = sum(doc.get("chunk_count", 0) for doc in documents)
avg_chunks = total_chunks / total_docs if total_docs > 0 else 0

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Documentos", total_docs)

with col2:
    st.metric("Total Chunks", total_chunks)

with col3:
    st.metric("Promedio Chunks/Doc", f"{avg_chunks:.1f}")

st.markdown("---")

# View options
st.subheader("📚 Lista de Documentos")

view_mode = st.radio(
    "Modo de visualización:",
    ["Tabla", "Tarjetas"],
    horizontal=True
)

# Search and filter
search_term = st.text_input("🔍 Buscar documento", placeholder="Escribe el nombre del documento...")

# Filter documents
filtered_docs = documents
if search_term:
    filtered_docs = [
        doc for doc in documents 
        if search_term.lower() in doc.get("filename", "").lower()
    ]

if view_mode == "Tabla":
    # Table view
    if filtered_docs:
        # Prepare data for table
        table_data = []
        for doc in filtered_docs:
            upload_date = datetime.fromisoformat(doc.get("upload_date", "").replace("Z", "+00:00"))
            table_data.append({
                "Nombre": doc.get("filename", ""),
                "Document ID": doc.get("document_id", "")[:8] + "...",
                "Fecha de Subida": upload_date.strftime("%Y-%m-%d %H:%M"),
                "Chunks": doc.get("chunk_count", 0)
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No se encontraron documentos con ese criterio de búsqueda.")

else:
    # Card view
    if filtered_docs:
        for doc in filtered_docs:
            doc_id = doc.get("document_id", "")
            filename = doc.get("filename", "")
            chunk_count = doc.get("chunk_count", 0)
            upload_date = datetime.fromisoformat(doc.get("upload_date", "").replace("Z", "+00:00"))
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### 📄 {filename}")
                    st.caption(f"**Document ID:** `{doc_id}`")
                    st.caption(f"**Fecha:** {upload_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.caption(f"**Chunks:** {chunk_count}")
                
                with col2:
                    # Actions
                    if st.button("ℹ️ Info", key=f"info_{doc_id}", use_container_width=True):
                        with st.expander(f"Detalles de {filename}", expanded=True):
                            st.json({
                                "document_id": doc_id,
                                "filename": filename,
                                "upload_date": doc.get("upload_date", ""),
                                "chunk_count": chunk_count
                            })
                    
                    if st.button("🔄 Reindexar", key=f"reindex_{doc_id}", use_container_width=True):
                        if reindex_document(doc_id, filename):
                            st.rerun()
                    
                    if st.button("🗑️ Eliminar", key=f"delete_{doc_id}", type="secondary", use_container_width=True):
                        st.session_state[f"confirm_delete_{doc_id}"] = True
                    
                    # Confirm deletion
                    if st.session_state.get(f"confirm_delete_{doc_id}", False):
                        st.warning("¿Estás seguro?")
                        col_yes, col_no = st.columns(2)
                        
                        with col_yes:
                            if st.button("Sí", key=f"yes_{doc_id}"):
                                if delete_document(doc_id, filename):
                                    st.session_state[f"confirm_delete_{doc_id}"] = False
                                    st.rerun()
                        
                        with col_no:
                            if st.button("No", key=f"no_{doc_id}"):
                                st.session_state[f"confirm_delete_{doc_id}"] = False
                                st.rerun()
                
                st.markdown("---")
    else:
        st.warning("No se encontraron documentos con ese criterio de búsqueda.")

# Bulk operations
st.markdown("---")
st.subheader("⚙️ Operaciones en Lote")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Reindexar Todos los Documentos", use_container_width=True):
        if st.session_state.get("confirm_reindex_all", False):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            for idx, doc in enumerate(documents):
                doc_id = doc.get("document_id", "")
                filename = doc.get("filename", "")
                status_text.text(f"Reindexando: {filename}")
                
                if reindex_document(doc_id, filename):
                    success_count += 1
                
                progress_bar.progress((idx + 1) / len(documents))
            
            st.success(f"✅ {success_count}/{len(documents)} documentos reindexados exitosamente")
            st.session_state["confirm_reindex_all"] = False
            st.cache_data.clear()
        else:
            st.session_state["confirm_reindex_all"] = True
            st.warning("⚠️ Esto reindexará TODOS los documentos. Haz clic de nuevo para confirmar.")

with col2:
    if st.button("🗑️ Eliminar Todos los Documentos", type="secondary", use_container_width=True):
        if st.session_state.get("confirm_delete_all", False):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            for idx, doc in enumerate(documents):
                doc_id = doc.get("document_id", "")
                filename = doc.get("filename", "")
                status_text.text(f"Eliminando: {filename}")
                
                if delete_document(doc_id, filename):
                    success_count += 1
                
                progress_bar.progress((idx + 1) / len(documents))
            
            st.success(f"✅ {success_count}/{len(documents)} documentos eliminados exitosamente")
            st.session_state["confirm_delete_all"] = False
            st.cache_data.clear()
            st.rerun()
        else:
            st.session_state["confirm_delete_all"] = True
            st.warning("⚠️ Esto ELIMINARÁ TODOS los documentos permanentemente. Haz clic de nuevo para confirmar.")

# Instructions
st.markdown("---")
with st.expander("📖 Guía de Uso"):
    st.markdown("""
    ### Gestión de Documentos
    
    Esta página te permite administrar todos los documentos indexados en el sistema.
    
    #### Operaciones disponibles:
    
    1. **Ver Documentos**: Visualiza todos los documentos con sus metadatos
    2. **Buscar**: Filtra documentos por nombre
    3. **Reindexar**: Vuelve a procesar un documento (útil si cambiaste la configuración de chunking)
    4. **Eliminar**: Borra un documento del sistema (archivo + vectores)
    5. **Operaciones en lote**: Reindexar o eliminar múltiples documentos a la vez
    
    #### Notas:
    
    - ⚠️ Eliminar un documento es permanente y no se puede deshacer
    - 🔄 Reindexar es útil cuando cambias parámetros de procesamiento
    - 📊 Las estadísticas se actualizan automáticamente
    """)