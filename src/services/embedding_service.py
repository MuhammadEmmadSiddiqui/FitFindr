"""Embedding service using BERT"""
import torch
from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from ..config import settings
from ..utils import get_logger


logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating and comparing text embeddings"""
    
    def __init__(self):
        """Initialize BERT model and tokenizer"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        logger.info(f"Loading BERT model: {settings.BERT_MODEL}")
        self.tokenizer = BertTokenizer.from_pretrained(settings.BERT_MODEL)
        self.model = BertModel.from_pretrained(settings.BERT_MODEL).to(self.device)
        self.model.eval()  # Set to evaluation mode
        logger.info("BERT model loaded successfully")
    
    def get_embeddings(self, text: str) -> np.ndarray:
        """
        Generate BERT embeddings for given text
        
        Args:
            text: Input text
            
        Returns:
            Numpy array of embeddings
        """
        with torch.no_grad():
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            ).to(self.device)
            
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1).detach().cpu().numpy()
        
        return embeddings
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        similarity = cosine_similarity(embedding1, embedding2)[0][0]
        return float(similarity)
    
    def compare_texts(self, text1: str, text2: str) -> float:
        """
        Compare two texts and return similarity score
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        emb1 = self.get_embeddings(text1)
        emb2 = self.get_embeddings(text2)
        return self.calculate_similarity(emb1, emb2)
