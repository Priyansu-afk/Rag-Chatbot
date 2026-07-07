from rag.chatbot import ChatbotService

svc = ChatbotService()
print("LLM model →", svc.llm.model_name)
