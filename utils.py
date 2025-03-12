import streamlit as st
from datetime import datetime
from config import MEDICAL_TOPICS

def track_interaction(query, response, tab):
    """
    Track user interactions for analytics purposes
    
    Args:
        query (str): The user's query
        response (str): The AI's response
        tab (str): Tab where the interaction occurred (General or Report)
    """
    # Track interaction count
    if tab == "General":
        st.session_state.analytics['general_interactions'] += 1
    else:
        st.session_state.analytics['document_interactions'] += 1
    
    # Track terms frequency (simple implementation)
    words = query.lower().split()
    for word in words:
        if len(word) > 3:  # Only count meaningful words
            if word in st.session_state.analytics['term_frequency']:
                st.session_state.analytics['term_frequency'][word] += 1
            else:
                st.session_state.analytics['term_frequency'][word] = 1
    
    # Track medical topics
    for topic in MEDICAL_TOPICS:
        if topic in query.lower():
            if topic in st.session_state.analytics['common_topics']:
                st.session_state.analytics['common_topics'][topic] += 1
            else:
                st.session_state.analytics['common_topics'][topic] = 1
    
    # Add to export history
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.export_history.append({
        "timestamp": timestamp,
        "type": tab,
        "query": query,
        "response": response
    })

def export_to_markdown():
    """Generate a markdown export of the conversation history"""
    
    if len(st.session_state.export_history) == 0:
        return "No conversation history to export."
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markdown = f"""# MediAssist Pro Conversation Export
Generated: {now}

## Conversation History

"""
    
    for item in st.session_state.export_history:
        markdown += f"### {item['timestamp']} - {item['type']} Query\n\n"
        markdown += f"**Question:** {item['query']}\n\n"
        markdown += f"**Response:** {item['response']}\n\n"
        markdown += "---\n\n"
    
    return markdown

def generate_clinical_summary(vector_store, chat_history):
    """
    Generate a clinical summary based on document content and conversation
    
    Args:
        vector_store: The document vector store
        chat_history: The conversation history
        
    Returns:
        str: A clinical summary
    """
    from gemini_handler import get_medical_response
    
    # Get a document sample
    doc_chunk = ""
    if vector_store and vector_store.chunks:
        doc_chunk = vector_store.chunks[0][:500]
    
    # Get conversation sample
    conv_sample = ""
    if len(chat_history) > 0:
        last_item = chat_history[-1]
        conv_sample = f"Q: {last_item['query']}\nA: {last_item['response'][:200]}..."
    
    # Generate report
    report_prompt = f"""
    Create a brief clinical summary report based on the document information
    and conversation history provided. Format it as a professional medical summary
    that could be shared with healthcare providers.
    
    DOCUMENT EXCERPT:
    {doc_chunk}
    
    CONVERSATION SAMPLE:
    {conv_sample}
    
    Create a concise, professional clinical summary with key findings and recommendations.
    """
    
    report = get_medical_response(report_prompt)
    return report

def create_document_folder():
    """Create documents folder if it doesn't exist"""
    import os
    if not os.path.exists("documents"):
        os.makedirs("documents")
        return True
    return False