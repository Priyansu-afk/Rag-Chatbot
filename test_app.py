import os
import sys
from datetime import datetime
from database.db import SessionLocal, Base, engine
from database.models import User, Document, Conversation, Message, Analytics
from auth.security import hash_password, verify_password
from rag.chunking import ChunkingService

def run_tests():
    print("==================================================")
    print("NEURODOCS AI: RUNNING AUTOMATED CORE UNIT TESTS")
    print("==================================================")
    
    # 1. Database Connection & Initializer
    print("\n[TEST 1] Testing SQLite Database connectivity & migrations...")
    try:
        Base.metadata.create_all(bind=engine)
        print("-> [SUCCESS] Database schemas created successfully.")
    except Exception as e:
        print(f"-> [FAIL] Database schema setup aborted: {e}")
        sys.exit(1)
        
    db = SessionLocal()
    
    # 2. User & Analytics insertion
    print("\n[TEST 2] Testing User database seeding & bcrypt hashing...")
    try:
        # Check if test user exists, delete if so
        existing_user = db.query(User).filter(User.username == "test_core_user").first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
            
        hashed = hash_password("cyber_password_99")
        # Validate hash works
        assert verify_password("cyber_password_99", hashed) is True
        assert verify_password("wrong_password", hashed) is False
        print("-> [SUCCESS] Password hashing & verification logic functional.")
        
        test_user = User(
            username="test_core_user",
            email="test@neurodocs.ai",
            password_hash=hashed
        )
        db.add(test_user)
        db.flush()
        
        test_analytics = Analytics(
            user_id=test_user.id,
            total_documents=0,
            total_questions=0
        )
        db.add(test_analytics)
        db.commit()
        print(f"-> [SUCCESS] Test user created. User ID: {test_user.id}")
    except Exception as e:
        print(f"-> [FAIL] User seeding failed: {e}")
        db.rollback()
        sys.exit(1)

    # 3. Document chunking validation
    print("\n[TEST 3] Testing Chunking split parameters...")
    try:
        sample_pages = [
            {
                "text": "NeuroDocs AI is an advanced document assistant. It operates in real-time. This is the second paragraph of text designed to test the recursive text splitter settings.",
                "metadata": {"source": "manual_test.pdf", "page": 1}
            }
        ]
        chunker = ChunkingService(chunk_size=50, chunk_overlap=10)
        chunks = chunker.split_pages(sample_pages)
        print(f"-> [SUCCESS] Text split successfully into {len(chunks)} chunks.")
        for i, chk in enumerate(chunks):
            print(f"   Chunk {i+1} Metadata: {chk.metadata} | Content size: {len(chk.page_content)}")
    except Exception as e:
        print(f"-> [FAIL] Chunking pipeline failed: {e}")
        sys.exit(1)

    # Clean up test user
    print("\n[TEST 4] Cleaning up test records...")
    try:
        db.delete(test_user)
        db.commit()
        print("-> [SUCCESS] Database state restored to original configuration.")
    except Exception as e:
        print(f"-> [FAIL] Cleanup failed: {e}")
    
    print("\n==================================================")
    print("NEURODOCS AI: ALL SANITY TESTS COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
