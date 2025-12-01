from openai import OpenAI
import google.generativeai as genai
from typing import List, Dict
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with LLM services.
    Supports OpenAI API and Google Gemini.
    """
    
    def __init__(self):
        settings = get_settings()
        self.provider = settings.LLM_PROVIDER
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        
        if self.provider == "openai":
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self.client = OpenAI(api_key=api_key)
            self.model = settings.OPENAI_MODEL
            logger.info(f"OpenAI client initialized with model: {self.model}")
        
        elif self.provider == "gemini":
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY not set in environment")
            
            # Configurar Gemini con la API key
            genai.configure(api_key=api_key)
            
            # CORREGIDO: Usar nombres de modelo correctos
            model_name = settings.GEMINI_MODEL
            
            # Mapeo de nombres de modelo
            model_mapping = {
                # Recommended modern models (use the short ID or the models/ prefix)
                "gemini-2.5-flash": "models/gemini-2.5-flash", 
                "gemini-2.5-pro": "models/gemini-2.5-pro",
                "gemini-flash": "models/gemini-2.5-flash", # Common alias
                # Legacy/older models may require specific version numbers if available
                # "gemini-pro" is deprecated; consider using a modern equivalent
            }
            
            # Si el usuario especificó un nombre corto, usar el mapeo
            if model_name in model_mapping:
                full_model_name = model_mapping[model_name]
            elif not model_name.startswith("models/"):
                # Si no tiene el prefijo, agregarlo
                full_model_name = f"models/{model_name}"
            else:
                full_model_name = model_name
            
            self.model = full_model_name
            
            try:
                self.gemini_model = genai.GenerativeModel(self.model)
                logger.info(f"Gemini client initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Error initializing Gemini model: {str(e)}")
                logger.info("Trying with gemini-pro as fallback...")
                self.model = "models/gemini-pro"
                self.gemini_model = genai.GenerativeModel(self.model)
                logger.info(f"Gemini client initialized with fallback model: {self.model}")
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def build_rag_prompt(
        self, 
        question: str, 
        context_chunks: List[Dict[str, any]]
    ) -> str:
        """
        Build a prompt for RAG with retrieved context.
        """
        context_text = "\n\n".join([
            f"[Fragmento {i+1}]:\n{chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        prompt = f"""Eres un asistente experto que responde preguntas basándose únicamente en la información proporcionada.

CONTEXTO RECUPERADO:
{context_text}

PREGUNTA DEL USUARIO:
{question}

INSTRUCCIONES:
1. Responde la pregunta usando ÚNICAMENTE la información del contexto proporcionado
2. Si la información no está en el contexto, indica claramente que no puedes responder con la información disponible
3. Sé preciso, claro y conciso
4. Cita el número de fragmento cuando sea relevante
5. Si hay información contradictoria, menciónalo

RESPUESTA:"""
        
        return prompt
    
    def generate_answer(
        self, 
        question: str, 
        context_chunks: List[Dict[str, any]]
    ) -> str:
        """
        Generate an answer using the LLM with retrieved context.
        """
        prompt = self.build_rag_prompt(question, context_chunks)
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un asistente experto en responder preguntas basándose en documentos institucionales."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                answer = response.choices[0].message.content.strip()
                return answer
            
            elif self.provider == "gemini":
                # Configurar parámetros de generación
                generation_config = {
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                    "top_p": 0.95,
                }
                
                # Configurar ajustes de seguridad (más permisivos para documentos técnicos)
                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_ONLY_HIGH"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_ONLY_HIGH"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_ONLY_HIGH"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_ONLY_HIGH"
                    },
                ]
                
                # Generar respuesta
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                # Verificar si hay respuesta
                if response.text:
                    return response.text.strip()
                else:
                    # Manejar casos donde Gemini bloquea la respuesta
                    if hasattr(response, 'prompt_feedback'):
                        logger.warning(f"Gemini blocked response: {response.prompt_feedback}")
                        return "Lo siento, la respuesta fue bloqueada por filtros de seguridad. Intenta reformular tu pregunta."
                    return "Lo siento, no pude generar una respuesta para esta consulta."
            
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def generate_simple_completion(self, prompt: str) -> str:
        """
        Generate a simple completion without RAG context.
        """
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                return response.choices[0].message.content.strip()
            
            elif self.provider == "gemini":
                generation_config = {
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                }
                
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                if response.text:
                    return response.text.strip()
                else:
                    return "No se pudo generar respuesta."
        
        except Exception as e:
            logger.error(f"Error in completion: {str(e)}")
            raise