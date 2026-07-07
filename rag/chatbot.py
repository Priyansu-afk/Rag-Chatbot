import os
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from database.models import Message, Conversation
from rag.vector_store import VectorStoreManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        # Read model name from environment, default to phi3 (free, local)
        model_name = os.getenv("OLLAMA_MODEL", "phi3")
        logger.info(f"Initializing local Ollama LLM with model: {model_name}")
        
        # Initialize the local Ollama Chat Model — no API key needed
        self.llm = ChatOllama(
            model=model_name,
            temperature=0.2,
            num_predict=2048,
        )
        self.vector_manager = VectorStoreManager()

    def _get_history(self, db: Session, conversation_id: int, limit: int = 10) -> List[Any]:
        """
        Retrieves the last `limit` messages from the database for the given conversation.
        """
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.asc())
            .all()
        )
        
        # Format into LangChain message objects
        history = []
        # Get last N messages
        recent_messages = messages[-limit:] if len(messages) > limit else messages
        for msg in recent_messages:
            if msg.role == "user":
                history.append(HumanMessage(content=msg.content))
            else:
                history.append(AIMessage(content=msg.content))
        return history

    def _format_context(self, search_results: List[Tuple[Any, float]]) -> str:
        """
        Combines search result snippets into a single context string.
        """
        context_parts = []
        for i, (doc, _) in enumerate(search_results):
            source = doc.metadata.get("source", "Unknown Document")
            page = doc.metadata.get("page", "?")
            context_parts.append(
                f"--- Document Source Chunk {i+1} [Source: {source} | Page: {page}] ---\n"
                f"{doc.page_content}"
            )
        return "\n\n".join(context_parts)

    def _format_citations(self, search_results: List[Tuple[Any, float]]) -> List[Dict[str, Any]]:
        """
        Formats search results into structured citations.
        """
        citations = []
        for doc, score in search_results:
            # Map L2 distance score from FAISS to a 0-100% confidence score.
            # L2 distance is typically 0 (exact match) up to 2.0 (opposite).
            # We map 0.0 -> 100%, 1.0 -> 50%, >= 1.5 -> ~0%
            relevance = max(0, int((1.0 - (score / 2.0)) * 100))
            citations.append({
                "source": doc.metadata.get("source", "Unknown Document"),
                "page": doc.metadata.get("page", "Unknown Page"),
                "snippet": doc.page_content,
                "score": relevance
            })
        return citations

    def get_quick_insights(self, file_path: str, doc_name: str) -> Dict[str, str]:
        """
        Generates document summaries, key points, FAQs, insights, and topics using OpenAI.
        """
        from rag.pdf_loader import PDFLoader
        
        # Load PDF text
        pages = PDFLoader.load_pdf(file_path)
        full_text = "\n".join([p["text"] for p in pages[:10]]) # Limit to first 10 pages to fit token limits gracefully
        
        prompt = (
            f"You are an AI document analysis system. Below is the text of the document named '{doc_name}'.\n"
            f"Analyze it and return a JSON structured object with the following fields:\n"
            f"1. 'summary': A professional, executive summary of the document (2-3 paragraphs).\n"
            f"2. 'key_points': A bulleted list of 5-7 key takeaways.\n"
            f"3. 'faqs': A list of 4 key questions and answers derived from the document.\n"
            f"4. 'insights': 3-4 deep analytical insights or critical findings.\n"
            f"5. 'topics': A comma-separated list of major topics discussed.\n\n"
            f"Do not include any code block formatting like ```json, return ONLY the raw JSON string.\n\n"
            f"Document Text:\n{full_text}"
        )
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            import json
            cleaned_response = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_response)
            return data
        except Exception as e:
            logger.error(f"Error generating insights for {doc_name}: {e}")
            msg = f"Failed to generate insights. Ensure Ollama is running (`ollama serve`). Details: {e}"
            return {
                "summary": msg,
                "key_points": [msg],
                "faqs": [{"q": "Error?", "a": msg}],
                "insights": [msg],
                "topics": "Error, Configuration"
            }

    def generate_response(
        self, 
        user_id: int, 
        conversation_id: int, 
        query: str, 
        db: Session
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieves context, constructs prompt history, calls LLM, and logs interaction.
        """
        # 1. Similarity search in FAISS
        # Fetch top 5 chunks
        search_results = self.vector_manager.similarity_search_with_score(user_id, query, k=5)
        
        citations = self._format_citations(search_results)
        context = self._format_context(search_results)
        
        # 2. Setup System Prompt with context
        system_template = (
            "You are NeuroDocs AI, a state-of-the-art document intelligence operating system.\n"
            "You provide precise, professional, and context-augmented answers based on the context files provided below.\n\n"
            f"--- CONTEXT TERMINAL ---\n"
            f"{context if context else 'NO DOCUMENT CONTEXT IS LOADED FOR THIS USER.'}\n"
            f"-----------------------\n\n"
            "INSTRUCTIONS:\n"
            "1. Answer the user's question USING ONLY the provided context blocks. Be extremely thorough.\n"
            "2. If the context does not contain the answer, say exactly: 'I cannot find that information in the uploaded documents. Please provide more documentation or refine your query.' Do not hallucinate or use external training knowledge to answer details not in the context.\n"
            "3. Cite specific document names and pages when presenting information (e.g. '[Source: document.pdf | Page: 3]').\n"
            "4. Adopt a professional, intelligent, slightly futuristic AI assistant tone."
        )
        
        # 3. Retrieve conversation history
        messages = [SystemMessage(content=system_template)]
        history = self._get_history(db, conversation_id, limit=8)
        messages.extend(history)
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # 4. Invoke LLM
        try:
            logger.info("Invoking local Ollama LLM for RAG response...")
            response = self.llm.invoke(messages)
            ai_response = response.content
        except Exception as e:
            logger.error(f"Error invoking Ollama LLM: {e}")
            ai_response = (
                "⚠️ **System Error**: Failed to get a response from the local AI model. "
                "Please ensure Ollama is running (`ollama serve`) and the model is pulled. "
                f"Details: {e}"
            )
            citations = []
        
        # 5. Save user and AI messages to SQLite
        try:
            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=query
            )
            ai_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_response
            )
            db.add(user_msg)
            db.add(ai_msg)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging messages to database: {e}")
            db.rollback()
            
        return ai_response, citations
