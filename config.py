import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

def init_session_state():
    """Initialize session state variables"""
    
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
        
    if 'documents_processed' not in st.session_state:
        st.session_state.documents_processed = False
        
    if 'general_chat_history' not in st.session_state:
        st.session_state.general_chat_history = []
        
    if 'report_chat_history' not in st.session_state:
        st.session_state.report_chat_history = []
        
    if 'show_starter_prompts' not in st.session_state:
        st.session_state.show_starter_prompts = True
        
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "General"
        
    if 'analytics' not in st.session_state:
        st.session_state.analytics = {
            'term_frequency': {},
            'document_interactions': 0,
            'general_interactions': 0,
            'common_topics': {},
            'session_start': datetime.now()
        }
        
    if 'extracted_insights' not in st.session_state:
        st.session_state.extracted_insights = []
        
    if 'medical_notes' not in st.session_state:
        st.session_state.medical_notes = []
        
    if 'export_history' not in st.session_state:
        st.session_state.export_history = []
        
    # Initialize API key in session state
    if 'api_key' not in st.session_state:
        st.session_state.api_key = get_api_key()

def get_api_key():
    """
    Get the API key from environment variables or session state
    
    Returns:
        str: The API key or None if not found
    """
    # Priority order for API key:
    # 1. Environment variable GEMINI_API_KEY (for production/deployment)
    # 2. Environment variable GOOGLE_API_KEY (alternative name)
    # 3. .env file variables (loaded via dotenv)
    # 4. Streamlit secrets (for Streamlit Cloud deployment)
    
    api_key = None
    
    # Check environment variables
    if os.environ.get("GEMINI_API_KEY"):
        api_key = os.environ.get("GEMINI_API_KEY")
    elif os.environ.get("GOOGLE_API_KEY"):
        api_key = os.environ.get("GOOGLE_API_KEY")
    
    # Check Streamlit secrets if available and API key not found yet
    if not api_key and hasattr(st, "secrets") and "api_keys" in st.secrets:
        api_key = st.secrets.api_keys.get("gemini_api_key")
    
    return api_key

# API Settings - will use function to get API key dynamically
API_SETTINGS = {
    "model_name": "models/gemini-2.0-flash"  # Adjust model name as needed
}

# App configuration
APP_CONFIG = {
    "app_name": "MediAssist Pro",
    "version": "1.0.0",
    "description": "Medical Document Intelligence Platform",
    "author": "Your Name",
    "copyright_year": "2025"
}

# Document processing settings
DOC_PROCESSING = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "max_insights": 3
}

# Medical topics for analytics
MEDICAL_TOPICS = [
    'diabetes', 'heart', 'blood pressure', 'cholesterol', 
    'medication', 'symptoms', 'treatment', 'diagnosis',
    'cancer', 'surgery', 'pain', 'infection'
]