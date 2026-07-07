import logging
import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def load_embeddings_model(model_name: str) -> HuggingFaceEmbeddings:
    """
    Loads and caches the HuggingFaceEmbeddings model using Streamlit's cache_resource.
    This ensures the model is only loaded into memory once across all reruns.
    """
    logger.info(f"Loading embedding model: {model_name}...")
    try:
        model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        logger.info("Embedding model loaded and cached successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise e

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Retrieves the cached HuggingFaceEmbeddings model.
        """
        self.embeddings = load_embeddings_model(model_name)

    def get_embedding_pipeline(self) -> HuggingFaceEmbeddings:
        """
        Returns the LangChain embedding implementation.
        """
        return self.embeddings
