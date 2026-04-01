import numpy as np
from typing import List
import logging
from sentence_transformers import SentenceTransformer
from shared.config import settings
from shared.exceptions import EmbeddingException

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""
    
    def __init__(self):
        """Initialize the embedding model."""
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.dimension = settings.VECTOR_DIMENSION
        self._initialize_model()
    
    def _initialize_model(self):
        """Load the embedding model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name} on {self.device}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # Verify model dimension matches configuration
            test_embedding = self.model.encode("test", normalize_embeddings=True)
            actual_dimension = len(test_embedding)
            
            if actual_dimension != self.dimension:
                logger.warning(
                    f"Model dimension mismatch: config={self.dimension}, actual={actual_dimension}. "
                    f"Updating config to match model."
                )
                # Update settings to match actual model dimension
                settings.VECTOR_DIMENSION = actual_dimension
                self.dimension = actual_dimension
            
            logger.info(f"Embedding model loaded successfully. Dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise EmbeddingException(f"Failed to load embedding model: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for the input text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List[float]: Embedding vector
            
        Raises:
            ValueError: If text is empty
            TypeError: If text is not a string
            EmbeddingException: If embedding generation fails
        """
        if not isinstance(text, str):
            raise TypeError(f"Expected string for embedding, got {type(text).__name__}")
        
        if not text.strip():
            raise ValueError("Cannot generate embedding for empty string")
        
        try:
            # Generate embedding
            embedding = self.model.encode(
                text,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            # Convert numpy array to list
            embedding_list = embedding.tolist()
            
            # Validate embedding
            if len(embedding_list) != self.dimension:
                raise EmbeddingException(
                    f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding_list)}"
                )
            
            if not all(isinstance(x, (int, float)) for x in embedding_list):
                raise EmbeddingException("Embedding contains non-numeric values")
            
            logger.debug(f"Generated embedding for text of length {len(text)}. Dimension: {len(embedding_list)}")
            return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            if isinstance(e, (ValueError, TypeError)):
                raise
            raise EmbeddingException(f"Failed to generate embedding: {e}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List[List[float]]: List of embedding vectors
            
        Raises:
            EmbeddingException: If embedding generation fails
        """
        if not texts:
            return []
        
        # Filter out empty strings
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            return []
        
        try:
            # Generate embeddings in batch
            embeddings = self.model.encode(
                valid_texts,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=32
            )
            
            # Convert to list of lists
            embeddings_list = [embedding.tolist() for embedding in embeddings]
            
            # Validate all embeddings
            for i, embedding in enumerate(embeddings_list):
                if len(embedding) != self.dimension:
                    raise EmbeddingException(
                        f"Embedding dimension mismatch at index {i}: "
                        f"expected {self.dimension}, got {len(embedding)}"
                    )
                
                if not all(isinstance(x, (int, float)) for x in embedding):
                    raise EmbeddingException(f"Embedding at index {i} contains non-numeric values")
            
            logger.debug(f"Generated {len(embeddings_list)} embeddings in batch")
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise EmbeddingException(f"Failed to generate batch embeddings: {e}")
    
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.dimension
    
    def get_model_info(self) -> dict:
        """Get information about the embedding model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dimension": self.dimension,
            "max_seq_length": self.model.max_seq_length
        }
