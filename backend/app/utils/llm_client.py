from openai import OpenAI
from typing import List, Dict
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with LLM services.
    Supports OpenAI API.
    """
    
    def __init__(self):
        settings = get_settings()
        self.provider = settings.LLM_PROVIDER
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        
        if self.provider == "openai":
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self.client = OpenAI(api_key=api_key)
            logger.info(f"OpenAI client initialized with model: {self.model}")
    
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
5. Si hay información contradictoria, mencionalo

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
            
        except Exception as e:
            logger.error(f"Error in completion: {str(e)}")
            raise