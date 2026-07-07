import os
import pypdf
from typing import List, Dict, Any

class PDFLoader:
    @staticmethod
    def load_pdf(file_path: str) -> List[Dict[str, Any]]:
        """
        Loads a PDF file and extracts text page by page.
        Returns a list of dictionaries with page content and metadata.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        pages_data = []
        doc_name = os.path.basename(file_path)

        try:
            reader = pypdf.PdfReader(file_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages_data.append({
                        "text": text.strip(),
                        "metadata": {
                            "source": doc_name,
                            "page": page_num + 1,  # 1-indexed for display
                            "file_path": file_path
                        }
                    })
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF file {doc_name}: {e}")

        return pages_data
