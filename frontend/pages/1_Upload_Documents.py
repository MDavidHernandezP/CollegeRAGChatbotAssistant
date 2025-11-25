import streamlit as st
import requests
import os
import time

# Page config
st.set_page_config(
    page_title="Upload Documents",
    page_icon="📤",
    layout="wide"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")

st.title("📤 Subir y Procesar Documentos")
st.markdown("---")

# Initialize session state
if 'uploaded_docs' not in st.session_state:
    st.session_state.uploaded_docs = []

# File uploader
st.subheader("1. Seleccionar Archivo PDF")
uploaded_file = st.file_uploader(
    "Arrastra o selecciona un archivo PDF",
    type=['pdf'],
    help="Solo se permiten archivos PDF. Tamaño máximo: 10MB"
)

if uploaded_file is not None:
    # Display file info
    file_details = {
        "Nombre": uploaded_file.name,
        "Tipo": uploaded_file.type,
        "Tamaño": f"{uploaded_file.size / 1024:.2f} KB"
    }
    
    st.info("📄 Archivo seleccionado")
    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre", file_details["Nombre"])
    col2.metric("Tipo", file_details["Tipo"])
    col3.metric("Tamaño", file_details["Tamaño"])
    
    st.markdown("---")
    
    # Upload and process options
    st.subheader("2. Opciones de Procesamiento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        process_immediately = st.checkbox(
            "Procesar inmediatamente después de subir",
            value=True,
            help="Si está marcado, el documento se indexará automáticamente"
        )
    
    with col2:
        show_progress = st.checkbox(
            "Mostrar progreso detallado",
            value=True,
            help="Muestra información detallada del proceso"
        )
    
    st.markdown("---")
    
    # Upload button
    if st.button("🚀 Subir Documento", type="primary", use_container_width=True):
        with st.spinner("Subiendo documento..."):
            try:
                # Prepare file for upload
                files = {
                    'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')
                }
                
                # Upload file
                upload_response = requests.post(
                    f"{API_BASE_URL}/documents/upload",
                    files=files,
                    timeout=60
                )
                
                if upload_response.status_code == 200:
                    upload_data = upload_response.json()
                    document_id = upload_data["document_id"]
                    filename = upload_data["filename"]
                    
                    st.success(f"✅ Documento subido exitosamente: {filename}")
                    st.info(f"📝 Document ID: `{document_id}`")
                    
                    # Add to session state
                    st.session_state.uploaded_docs.append({
                        "document_id": document_id,
                        "filename": filename,
                        "upload_time": time.time()
                    })
                    
                    # Process if option is selected
                    if process_immediately:
                        st.markdown("---")
                        st.subheader("3. Procesando Documento")
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            # Step 1: Extract text
                            if show_progress:
                                status_text.text("📖 Extrayendo texto del PDF...")
                                progress_bar.progress(20)
                                time.sleep(0.5)
                            
                            # Step 2: Chunking
                            if show_progress:
                                status_text.text("✂️ Dividiendo texto en fragmentos...")
                                progress_bar.progress(40)
                                time.sleep(0.5)
                            
                            # Step 3: Generate embeddings and index
                            status_text.text("🔄 Generando embeddings e indexando...")
                            progress_bar.progress(60)
                            
                            ingest_response = requests.post(
                                f"{API_BASE_URL}/ingest/process",
                                json={
                                    "document_id": document_id,
                                    "filename": filename
                                },
                                timeout=300
                            )
                            
                            progress_bar.progress(80)
                            
                            if ingest_response.status_code == 200:
                                ingest_data = ingest_response.json()
                                progress_bar.progress(100)
                                status_text.text("✅ ¡Procesamiento completado!")
                                
                                st.success("🎉 Documento procesado e indexado exitosamente")
                                
                                # Display processing stats
                                st.subheader("📊 Estadísticas de Procesamiento")
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric(
                                        "Chunks Procesados",
                                        ingest_data.get("chunks_processed", 0)
                                    )
                                
                                with col2:
                                    st.metric(
                                        "Embeddings Creados",
                                        ingest_data.get("embeddings_created", 0)
                                    )
                                
                                with col3:
                                    st.metric(
                                        "Estado",
                                        "Completado" if ingest_data.get("success") else "Error"
                                    )
                                
                                st.balloons()
                                
                            else:
                                st.error(f"❌ Error procesando documento: {ingest_response.text}")
                        
                        except requests.exceptions.Timeout:
                            st.error("⏱️ Timeout procesando documento. El documento es muy grande o el servidor está ocupado.")
                        except Exception as e:
                            st.error(f"❌ Error durante el procesamiento: {str(e)}")
                    
                    else:
                        st.info("💡 Documento subido pero no procesado. Ve a la página 'Manage Documents' para procesarlo.")
                
                else:
                    error_detail = upload_response.json().get("detail", "Error desconocido")
                    st.error(f"❌ Error subiendo documento: {error_detail}")
            
            except requests.exceptions.Timeout:
                st.error("⏱️ Timeout subiendo documento. El archivo es muy grande.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Show recently uploaded documents
st.markdown("---")
st.subheader("📋 Documentos Subidos en esta Sesión")

if st.session_state.uploaded_docs:
    for idx, doc in enumerate(reversed(st.session_state.uploaded_docs[-5:])):
        with st.expander(f"📄 {doc['filename']}"):
            st.code(f"Document ID: {doc['document_id']}")
            st.text(f"Subido hace: {int(time.time() - doc['upload_time'])} segundos")
else:
    st.info("No hay documentos subidos en esta sesión aún.")

# Instructions
st.markdown("---")
st.subheader("📖 Instrucciones")

st.markdown("""
### Cómo usar esta página:

1. **Selecciona un archivo PDF** usando el selector de archivos
2. **Configura las opciones** de procesamiento según tus necesidades
3. **Haz clic en "Subir Documento"** para comenzar
4. **Espera el procesamiento** (si está habilitado) - puede tomar varios minutos para documentos grandes
5. **Ve a "Ask Questions"** para comenzar a hacer preguntas sobre tus documentos

### Notas importantes:

- ✅ Solo se aceptan archivos PDF
- ✅ Tamaño máximo: 10MB por archivo
- ✅ El procesamiento puede tardar según el tamaño del documento
- ✅ Los documentos quedan disponibles permanentemente hasta que los elimines
- ✅ Puedes subir múltiples documentos y consultar todos a la vez
""")

# Tips
st.markdown("---")
st.info("""
💡 **Tip**: Para mejores resultados, asegúrate de que tus PDFs:
- Tengan texto seleccionable (no sean solo imágenes escaneadas)
- Estén bien estructurados con párrafos claros
- No tengan mucho contenido en tablas complejas
""")