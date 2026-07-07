import os
import shutil
from datetime import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import User, Document, Conversation, Message, Analytics
from ui.components import (
    neon_header, glass_card_start, glass_card_end, 
    metric_card, citation_block, user_profile, holographic_loader
)
from rag.pdf_loader import PDFLoader
from rag.chunking import ChunkingService
from rag.vector_store import VectorStoreManager
from rag.chatbot import ChatbotService

class Dashboard:
    def __init__(self):
        self.vector_manager = VectorStoreManager()
        self.chunker = ChunkingService()
        self.chatbot = ChatbotService()
        
        # Ensure uploads folder exists
        os.makedirs("uploads", exist_ok=True)

    def _get_user_upload_dir(self, user_id: int) -> str:
        path = os.path.join("uploads", f"user_{user_id}")
        os.makedirs(path, exist_ok=True)
        return path

    def render(self):
        """
        Renders the entire dashboard UI.
        """
        user_id = st.session_state.user_id
        username = st.session_state.username
        
        db = SessionLocal()
        try:
            # 1. Fetch user data and stats
            user = db.query(User).filter(User.id == user_id).first()
            analytics = db.query(Analytics).filter(Analytics.user_id == user_id).first()
            if not analytics:
                analytics = Analytics(user_id=user_id, total_documents=0, total_questions=0)
                db.add(analytics)
                db.commit()
                db.refresh(analytics)
                
            docs = db.query(Document).filter(Document.user_id == user_id).all()
            conversations = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).all()
            
            # Setup sidebar elements
            self.render_sidebar(db, user, analytics, docs, conversations)
            
            # Setup main dashboard tabs
            neon_header("NEURODOCS AI", "INTELLIGENT DOCUMENT OS v1.0")
            
            # Model info banner
            ollama_model = os.getenv("OLLAMA_MODEL", "phi3")
            st.info(f"🧠 **AI Core**: Running locally with Ollama model `{ollama_model}` — no API key needed.")
            
            tab1, tab2, tab3 = st.tabs([
                "💬 COGNITIVE CHAT ROOM", 
                "🧠 DOCUMENT INTELLIGENCE TOOLS", 
                "📊 SYSTEM ANALYTICS"
            ])
            
            with tab1:
                self.render_chat_tab(db, user_id, conversations)
                
            with tab2:
                self.render_doc_tools_tab(db, user_id, docs)
                
            with tab3:
                self.render_analytics_tab(db, user_id, docs, analytics)
                
        finally:
            db.close()

    def render_sidebar(
        self, 
        db: Session, 
        user: User, 
        analytics: Analytics, 
        docs: list, 
        conversations: list
    ):
        """
        Renders the sidebar navigation, uploads, and conversation selector.
        """
        with st.sidebar:
            # Title & Avatar
            user_profile(user.username, user.email)
            
            # Logout
            if st.button("TERMINATE SESSION (LOGOUT)", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.active_conv_id = None
                st.rerun()
            
            st.markdown("---")
            
            # Document uploader
            st.markdown("<h3 style='font-family: Orbitron; font-size: 0.95rem; color:#00f0ff;'>PDF INGESTION PORTAL</h3>", unsafe_allow_html=True)
            uploaded_files = st.file_uploader(
                "Upload document modules (PDF)", 
                type=["pdf"], 
                accept_multiple_files=True,
                label_visibility="collapsed"
            )
            
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    # Check if file exists in DB
                    exists = db.query(Document).filter(
                        Document.user_id == user.id, 
                        Document.document_name == uploaded_file.name
                    ).first()
                    
                    if not exists:
                        with st.spinner(f"Ingesting {uploaded_file.name}..."):
                            # Save to disk
                            user_dir = self._get_user_upload_dir(user.id)
                            file_path = os.path.join(user_dir, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Add to database
                            new_doc = Document(
                                user_id=user.id,
                                document_name=uploaded_file.name,
                                file_path=file_path,
                                upload_date=datetime.utcnow()
                            )
                            db.add(new_doc)
                            db.flush()
                            
                            # Process PDF and add to FAISS
                            try:
                                pages_data = PDFLoader.load_pdf(file_path)
                                if pages_data:
                                    chunks = self.chunker.split_pages(pages_data)
                                    self.vector_manager.add_documents(user.id, chunks)
                                    
                                    # Update analytics
                                    analytics.total_documents = len(docs) + 1
                                    analytics.last_activity = datetime.utcnow()
                                    db.commit()
                                    st.success(f"{uploaded_file.name} indexed.")
                                    st.rerun()
                                else:
                                    st.warning(f"No text extracted from {uploaded_file.name}.")
                            except Exception as e:
                                db.rollback()
                                st.error(f"Failed to process {uploaded_file.name}: {e}")
            
            st.markdown("---")
            
            # Document list with delete option
            st.markdown("<h3 style='font-family: Orbitron; font-size: 0.95rem; color:#00f0ff;'>INGESTED MODULES</h3>", unsafe_allow_html=True)
            if not docs:
                st.markdown("<p style='font-size:0.8rem; color:#8b949e;'>No modules ingested yet.</p>", unsafe_allow_html=True)
            else:
                for doc in docs:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"<p style='font-size:0.8rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin-bottom:0;'>📄 {doc.document_name}</p>", unsafe_allow_html=True)
                    with col2:
                        # Cyberpunk red delete button
                        if st.button("❌", key=f"del_{doc.id}", help="Purge document from vector database"):
                            self.delete_document(db, user.id, doc, analytics)
                            st.rerun()
            
            st.markdown("---")
            
            # Conversations list
            st.markdown("<h3 style='font-family: Orbitron; font-size: 0.95rem; color:#00f0ff;'>SESSION HISTORY</h3>", unsafe_allow_html=True)
            if st.button("+ INITIALIZE NEW CHAT", use_container_width=True, key="new_chat_btn"):
                # Create conversation
                new_conv = Conversation(
                    user_id=user.id,
                    title=f"Session @ {datetime.now().strftime('%H:%M:%S')}",
                    created_at=datetime.utcnow()
                )
                db.add(new_conv)
                db.commit()
                st.session_state.active_conv_id = new_conv.id
                st.rerun()
                
            if not conversations:
                st.markdown("<p style='font-size:0.8rem; color:#8b949e;'>No active sessions.</p>", unsafe_allow_html=True)
            else:
                for conv in conversations:
                    # Highlight active conversation
                    is_active = (st.session_state.get("active_conv_id") == conv.id)
                    btn_label = f"💬 {conv.title}"
                    btn_type = "primary" if is_active else "secondary"
                    if is_active:
                        btn_label = f"▶ {conv.title.upper()}"
                        
                    if st.button(btn_label, key=f"conv_{conv.id}", use_container_width=True, type=btn_type):
                        st.session_state.active_conv_id = conv.id
                        st.rerun()

    def delete_document(self, db: Session, user_id: int, doc: Document, analytics: Analytics):
        """
        Deletes the document from DB, filesystem, and updates vector index.
        """
        try:
            # Delete from filesystem
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
            
            db.delete(doc)
            db.commit()
            
            # Fetch remaining documents to rebuild FAISS index
            remaining_docs = db.query(Document).filter(Document.user_id == user_id).all()
            analytics.total_documents = len(remaining_docs)
            analytics.last_activity = datetime.utcnow()
            db.commit()
            
            # Clear old vector store index
            self.vector_manager.delete_user_index(user_id)
            
            # Rebuild vector store from scratch using remaining docs
            if remaining_docs:
                all_chunks = []
                for r_doc in remaining_docs:
                    pages = PDFLoader.load_pdf(r_doc.file_path)
                    chunks = self.chunker.split_pages(pages)
                    all_chunks.extend(chunks)
                
                if all_chunks:
                    self.vector_manager.add_documents(user_id, all_chunks)
            
            st.success("Document purged from index.")
        except Exception as e:
            st.error(f"Error purging document: {e}")

    def render_chat_tab(self, db: Session, user_id: int, conversations: list):
        """
        Renders the conversation chat space.
        """
        # Ensure we have an active conversation selected
        if not st.session_state.get("active_conv_id"):
            if conversations:
                st.session_state.active_conv_id = conversations[0].id
            else:
                # Create a default conversation
                new_conv = Conversation(
                    user_id=user_id,
                    title="Workspace Session",
                    created_at=datetime.utcnow()
                )
                db.add(new_conv)
                db.commit()
                st.session_state.active_conv_id = new_conv.id
                
        active_conv_id = st.session_state.active_conv_id
        
        # Load conversation details
        conv = db.query(Conversation).filter(Conversation.id == active_conv_id).first()
        if not conv:
            st.session_state.active_conv_id = None
            st.rerun()
            
        glass_card_start(f"NEURAL INTERACTION CENTER: {conv.title.upper()}", depth=True)
        
        # Action bar
        col1, col2 = st.columns([2, 1])
        with col1:
            new_title = st.text_input("RENAME SESSION", value=conv.title, key="rename_conv", label_visibility="collapsed")
            if new_title != conv.title and new_title.strip() != "":
                conv.title = new_title
                db.commit()
                st.rerun()
        with col2:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("🧹 PURGE", use_container_width=True, help="Purge all messages in this session"):
                    db.query(Message).filter(Message.conversation_id == active_conv_id).delete()
                    db.commit()
                    st.rerun()
            with btn_col2:
                if st.button("🗑️ DELETE", use_container_width=True, help="Delete this session"):
                    # Check if there are other sessions
                    all_convs = db.query(Conversation).filter(Conversation.user_id == user_id).all()
                    if len(all_convs) <= 1:
                        st.warning("Cannot delete the last remaining session.")
                    else:
                        db.query(Message).filter(Message.conversation_id == active_conv_id).delete()
                        db.query(Conversation).filter(Conversation.id == active_conv_id).delete()
                        db.commit()
                        st.session_state.active_conv_id = None
                        st.rerun()
                
        glass_card_end()
        
        # Quick Actions Helper
        st.markdown("<p style='font-size:0.85rem; color:#8b949e; margin-bottom:5px;'>QUICK ACTION INQUIRIES:</p>", unsafe_allow_html=True)
        cols = st.columns(4)
        quick_prompts = [
            "Summarize all files",
            "What are the main risks?",
            "Identify key entities",
            "List core definitions"
        ]
        
        selected_quick_prompt = None
        for i, prompt_text in enumerate(quick_prompts):
            with cols[i]:
                if st.button(prompt_text, key=f"qp_{i}", use_container_width=True):
                    selected_quick_prompt = prompt_text
        
        # Load past messages
        messages = db.query(Message).filter(Message.conversation_id == active_conv_id).order_by(Message.timestamp.asc()).all()
        
        chat_container = st.container()
        with chat_container:
            if not messages:
                st.chat_message("assistant").write("Systems online. Upload documents to query them. Enter a command or query to proceed.")
            for msg in messages:
                st.chat_message(msg.role).write(msg.content)
                
        # Chat Input
        user_query = st.chat_input("Enter cognitive inquiry...")
        
        # If user used a quick action prompt
        if selected_quick_prompt:
            user_query = selected_quick_prompt
            
        if user_query:
            # Render user message instantly
            with chat_container:
                st.chat_message("user").write(user_query)
            
            # Processing holographic loader
            with st.spinner("Decrypting database & querying AI core..."):
                holographic_loader()
                
                # Fetch RAG Response
                ai_response, citations = self.chatbot.generate_response(user_id, active_conv_id, user_query, db)
                
                # Update stats
                analytics = db.query(Analytics).filter(Analytics.user_id == user_id).first()
                if analytics:
                    analytics.total_questions += 1
                    analytics.last_activity = datetime.utcnow()
                    db.commit()
                
                # Rerun to show updated conversation
                st.rerun()

        # Display source citations side-card if citations exist in the last message
        if messages:
            last_message = messages[-1]
            if last_message.role == "assistant":
                # Get citations for the last message
                # To do this cleanly, we'll re-run a similarity search for the user's last query (which is second to last message in the DB)
                last_user_messages = [m for m in messages if m.role == "user"]
                if last_user_messages:
                    last_query = last_user_messages[-1].content
                    # Run search to get documents that were used
                    search_results = self.vector_manager.similarity_search_with_score(user_id, last_query, k=3)
                    citations = self.chatbot._format_citations(search_results)
                    
                    if citations:
                        st.markdown("<br>", unsafe_allow_html=True)
                        glass_card_start("SOURCE CITATIONS MATRIX")
                        for cit in citations:
                            citation_block(cit)
                        glass_card_end()

    def render_doc_tools_tab(self, db: Session, user_id: int, docs: list):
        """
        Renders AI tools like summarizers and FAQ extraction per document.
        """
        glass_card_start("AI DOCUMENT ANALYSIS LAB")
        st.markdown("<p style='color:#8b949e; font-size:0.9rem;'>Select an uploaded document to extract deep neural intelligence, FAQs, summaries, or structured insights.</p>", unsafe_allow_html=True)
        
        if not docs:
            st.info("No documents uploaded yet. Go to the sidebar Ingestion Portal to upload a PDF.")
            glass_card_end()
            return
            
        doc_names = [d.document_name for d in docs]
        selected_name = st.selectbox("SELECT MODULE FOR COGNITIVE INSIGHTS", doc_names)
        
        selected_doc = next(d for d in docs if d.document_name == selected_name)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            summarize_btn = st.button("GENERATE EXECUTIVE SUMMARY", use_container_width=True)
            faq_btn = st.button("EXTRACT KEY FAQs", use_container_width=True)
        with col2:
            keypoints_btn = st.button("EXTRACT TAKEAWAYS & TOPICS", use_container_width=True)
            deep_insights_btn = st.button("RUN DEEP INSIGHT ENGINE", use_container_width=True)
            
        if summarize_btn or faq_btn or keypoints_btn or deep_insights_btn:
            with st.spinner("Synthesizing document text with local AI model..."):
                holographic_loader()
                
                # Fetch summary/metadata
                insights_data = self.chatbot.get_quick_insights(selected_doc.file_path, selected_doc.document_name)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if summarize_btn:
                    st.subheader("Executive Summary")
                    st.write(insights_data.get("summary", "Summary unavailable."))
                elif faq_btn:
                    st.subheader("Frequently Asked Questions")
                    faqs = insights_data.get("faqs", [])
                    if isinstance(faqs, list):
                        for faq in faqs:
                            if isinstance(faq, dict):
                                st.markdown(f"**Q: {faq.get('q', faq.get('question', ''))}**")
                                st.markdown(f"A: {faq.get('a', faq.get('answer', ''))}")
                            else:
                                st.write(faq)
                    else:
                        st.write(faqs)
                elif keypoints_btn:
                    st.subheader("Key Takeaways & Core Topics")
                    key_points = insights_data.get("key_points", "")
                    if isinstance(key_points, list):
                        for kp in key_points:
                            st.markdown(f"* {kp}")
                    else:
                        st.write(key_points)
                        
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"**Extracted Topics:** `{insights_data.get('topics', 'None')}`")
                elif deep_insights_btn:
                    st.subheader("Deep Analytical Insights")
                    insights = insights_data.get("insights", "")
                    if isinstance(insights, list):
                        for ins in insights:
                            st.markdown(f"💡 {ins}")
                    else:
                        st.write(insights)
                        
        glass_card_end()

    def render_analytics_tab(self, db: Session, user_id: int, docs: list, analytics: Analytics):
        """
        Renders the database metrics, usage dashboard, and Plotly visualization.
        """
        glass_card_start("SYSTEM CONTROL & METRICS")
        
        # 3 Metrics side-by-side
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_card("INGESTED DOCUMENTS", analytics.total_documents)
        with col2:
            metric_card("COGNITIVE QUESTIONS ASKED", analytics.total_questions)
        with col3:
            last_act_str = analytics.last_activity.strftime("%Y-%m-%d %H:%M") if analytics.last_activity else "Never"
            metric_card("LAST NETWORK ACTIVITY", last_act_str)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charting section
        st.markdown("<h3 class='section-title'>DOCUMENT SIZE & VOLUME MATRIX</h3>", unsafe_allow_html=True)
        if not docs:
            st.info("No documents are currently indexed. Upload files to see analytics visualization.")
        else:
            # Build data frame for plotly
            chart_data = []
            for d in docs:
                size_kb = 0
                if os.path.exists(d.file_path):
                    size_kb = round(os.path.getsize(d.file_path) / 1024, 2)
                
                chart_data.append({
                    "Document Name": d.document_name,
                    "Size (KB)": size_kb,
                    "Ingestion Date": d.upload_date.strftime("%Y-%m-%d")
                })
            
            # Bar Chart: Document Sizes
            fig1 = px.bar(
                chart_data, 
                x="Document Name", 
                y="Size (KB)",
                title="Document Footprint Index (Size in KB)",
                template="plotly_dark",
                color="Size (KB)",
                color_continuous_scale=["#0072ff", "#00f0ff"]
            )
            fig1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="Share Tech Mono",
                font_color="#00f0ff"
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Bubble/Scatter: Ingestion Timeline
            fig2 = px.scatter(
                chart_data, 
                x="Ingestion Date", 
                y="Size (KB)",
                size="Size (KB)",
                hover_name="Document Name",
                title="Chronological Ingestion Activity Stream",
                template="plotly_dark",
                color_discrete_sequence=["#00f0ff"]
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="Share Tech Mono",
                font_color="#00f0ff"
            )
            st.plotly_chart(fig2, use_container_width=True)

        glass_card_end()
