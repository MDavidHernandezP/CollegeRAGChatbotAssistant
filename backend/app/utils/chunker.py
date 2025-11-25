import re
from typing import List, Tuple
from app.config import get_settings


class TextChunker:
    """
    Advanced text chunker with overlapping windows for better context preservation.
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        settings = get_settings()
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.,;:!?()-]', '', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text
    
    def chunk_by_sentences(self, text: str) -> List[str]:
        """
        Split text into chunks based on sentences with overlap.
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence.split())
            
            # If single sentence exceeds chunk_size, split it
            if sentence_size > self.chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split long sentence into smaller parts
                words = sentence.split()
                for i in range(0, len(words), self.chunk_size):
                    chunk_words = words[i:i + self.chunk_size]
                    chunks.append(' '.join(chunk_words))
                continue
            
            # Check if adding sentence exceeds chunk_size
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                
                # Calculate overlap
                overlap_size = 0
                overlap_sentences = []
                for s in reversed(current_chunk):
                    s_size = len(s.split())
                    if overlap_size + s_size <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += s_size
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_size = overlap_size
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def chunk_text(self, text: str) -> List[Tuple[str, int]]:
        """
        Main chunking method that returns chunks with their indices.
        """
        cleaned_text = self.clean_text(text)
        chunks = self.chunk_by_sentences(cleaned_text)
        
        # Filter out very small chunks
        min_chunk_size = 20  # minimum words
        filtered_chunks = [
            (chunk, idx) 
            for idx, chunk in enumerate(chunks) 
            if len(chunk.split()) >= min_chunk_size
        ]
        
        return filtered_chunks