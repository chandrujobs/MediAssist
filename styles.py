import streamlit as st

def load_css():
    """Load CSS styles for the application"""
    
    st.markdown("""
    <style>
        /* Main container adjustments */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* Welcome message container */
        .welcome-container {
            margin-bottom: 1rem;
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #f5f7fa;
            border-left: 4px solid #2e7d32;
        }
        
        /* Style chat messages */
        .stChatMessage {
            padding: 0.5rem 0;
        }
        
        /* Make the chat message content wider */
        .stChatMessage [data-testid="stChatMessageContent"] {
            width: 80%;
        }
        
        /* USP feature container */
        .usp-container {
            background-color: #f0f7ff;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid #d0e0f0;
        }
        
        /* Feature cards */
        .feature-card {
            background-color: white;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 0.8rem;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Feature icon */
        .feature-icon {
            font-size: 1.5rem;
            margin-right: 0.5rem;
            color: #2e7d32;
        }
        
        /* About app sections */
        .about-section {
            margin-bottom: 2rem;
        }
        
        /* Fix tabs position and styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 10px 16px;
            white-space: pre-wrap;
            background-color: #f5f7fa;
            border-radius: 4px 4px 0 0;
            font-size: 14px;
            font-weight: 500;
            border: 1px solid #e0e0e0;
            border-bottom: none;
            margin-right: 4px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #2e7d32 !important;
            color: white !important;
            border-color: #2e7d32 !important;
        }
        
        .stTabs [data-baseweb="tab-content"] {
            padding: 1rem;
            border: 1px solid #e0e0e0;
            border-radius: 0 4px 4px 4px;
        }
        
        /* Query input section styling */
        .chat-input-section {
            background-color: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        
        /* Buttons styling */
        .stButton button {
            font-weight: 500;
        }
        
        .stButton button:hover {
            background-color: #e8f0fe !important;
            color: #174ea6 !important;
            border-color: #174ea6 !important;
        }
        
        .stButton button[data-baseweb="button"][kind="primary"] {
            background-color: #2e7d32;
        }
        
        .stButton button[data-baseweb="button"][kind="primary"]:hover {
            background-color: #1b5e20 !important;
            color: white !important;
        }
        
        .stButton button[data-baseweb="button"][kind="secondary"] {
            border-color: #2e7d32;
            color: #2e7d32;
        }
        
        /* Disclaimer styling */
        .disclaimer {
            font-size: 0.8rem;
            color: #666;
            padding: 0.5rem;
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            margin-top: 0.5rem;
        }
        
        /* Hide default Streamlit footer */
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)