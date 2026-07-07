import os
import shutil
import logging
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from rag.embeddings import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, base_dir: str = "vectorstore"):
        self.base_dir = base_dir
        self.embedding_service = EmbeddingService()
        self.embeddings = self.embedding_service.get_embedding_pipeline()
        
        # Ensure base directory exists
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_user_index_path(self, user_id: int) -> str:
        """
        Returns the path to the user's specific FAISS index folder.
        """
        return os.path.join(self.base_dir, f"user_{user_id}")

    def index_exists(self, user_id: int) -> bool:
        """
        Checks if a FAISS index exists for the specified user.
        """
        user_path = self._get_user_index_path(user_id)
        return os.path.exists(os.path.join(user_path, "index.faiss"))

    def get_vector_store(self, user_id: int) -> Optional[FAISS]:
        """
        Loads the user's local FAISS vector store.
        """
        if not self.index_exists(user_id):
            return None
        
        user_path = self._get_user_index_path(user_id)
        try:
            return FAISS.load_local(
                user_path, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            logger.error(f"Error loading FAISS index for user {user_id}: {e}")
            return None

    def add_documents(self, user_id: int, new_documents: List[Document]) -> None:
        """
        Appends new document chunks to the user's FAISS index.
        Creates a new index if none exists.
        """
        if not new_documents:
            return

        user_path = self._get_user_index_path(user_id)
        vector_store = self.get_vector_store(user_id)

        try:
            if vector_store is None:
                logger.info(f"Creating new FAISS vector store index for user {user_id}...")
                vector_store = FAISS.from_documents(new_documents, self.embeddings)
            else:
                logger.info(f"Adding documents to existing FAISS vector store index for user {user_id}...")
                vector_store.add_documents(new_documents)
            
            vector_store.save_local(user_path)
            logger.info(f"Successfully saved FAISS index for user {user_id} at {user_path}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index for user {user_id}: {e}")
            raise e

    def delete_user_index(self, user_id: int) -> None:
        """
        Deletes the user's FAISS directory entirely.
        """
        user_path = self._get_user_index_path(user_id)
        if os.path.exists(user_path):
            try:
                shutil.rmtree(user_path)
                logger.info(f"Deleted vector index for user {user_id} at {user_path}")
            except Exception as e:
                logger.error(f"Error deleting vector store directory for user {user_id}: {e}")

    def similarity_search_with_score(self, user_id: int, query: str, k: int = 4) -> List[tuple]:
        """
        Searches the user's vector store for semantic matches.
        Returns a list of (Document, score) tuples.
        """
        vector_store = self.get_vector_store(user_id)
        if not vector_store:
            return []
        
        try:
            # FAISS similarity search returns (Document, L2 distance score)
            # A lower L2 score means closer similarity. We can normalize or just present the raw distance/relevance.
            return vector_store.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"Search failure for user {user_id}: {e}")
            return []
