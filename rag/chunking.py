from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class ChunkingService:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def split_pages(self, pages_data: List[Dict[str, Any]]) -> List[Document]:
        """
        Splits pages_data (from PDFLoader) into LangChain Document chunks.
        Applies metadata (source document name, page, file_path) to each chunk.
        """
        documents = []
        for page in pages_data:
            chunks = self.splitter.split_text(page["text"])
            for index, chunk in enumerate(chunks):
                # We can add specific chunk index to metadata if needed
                meta = page["metadata"].copy()
                meta["chunk_id"] = index
                documents.append(Document(page_content=chunk, metadata=meta))
        
        return documents
