import streamlit as st
import google.generativeai as genai
from config import API_SETTINGS

def get_api_key():
    """Get the API key from session state"""
    if 'api_key' in st.session_state and st.session_state.api_key:
        return st.session_state.api_key
    return None

def get_model():
    """Get the Gemini model"""
    api_key = get_api_key()
    
    if not api_key:
        return None
    
    try:
        # Configure with the API key
        genai.configure(api_key=api_key)
        
        # Get the model
        model = genai.GenerativeModel(API_SETTINGS["model_name"])
        return model
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        return None

def get_medical_response(query, context=None):
    """
    Generate a response to a medical query using the Gemini model
    
    Args:
        query (str): The user's query
        context (str, optional): Document context for the query
        
    Returns:
        str: The generated response
    """
    model = get_model()
    
    if not model:
        return "⚠️ API key is missing or invalid. Please add your Gemini API key in the sidebar settings."
    
    try:
        # If we have context from relevant documents
        if context:
            prompt = f"""
            You are an AI medical assistant. Answer the following health-related question 
            based on the provided medical context. Be accurate, helpful, and clear.
            
            MEDICAL CONTEXT:
            {context}
            
            USER QUESTION:
            {query}
            
            When answering:
            1. Cite specific information from the context when possible
            2. If the context doesn't contain relevant information, say so clearly
            3. Never make up medical information
            4. Include appropriate disclaimers about consulting healthcare professionals when necessary
            """
        else:
            # Generic medical assistant prompt when no specific context is provided
            prompt = f"""
            You are an AI medical assistant. Answer the following health-related question 
            to the best of your knowledge. Be accurate, helpful, and clear.
            
            USER QUESTION:
            {query}
            
            When answering:
            1. Only share well-established medical information
            2. If you're unsure, say so clearly
            3. Never make up medical information
            4. Include appropriate disclaimers about consulting healthcare professionals when necessary
            """
        
        # Generate the response
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(error_message)
        return f"⚠️ {error_message}"

def check_api_status():
    """
    Check if the Gemini API is properly configured and working
    
    Returns:
        dict: Status information about the API
    """
    model = get_model()
    
    if not model:
        return {
            "status": "error",
            "message": "API key missing or invalid. Please add your Gemini API key."
        }
    
    try:
        # Test with a simple prompt
        response = model.generate_content("Reply with 'API test successful' if you can read this message.")
        
        if "API test successful" in response.text:
            return {
                "status": "success",
                "message": "Gemini API is properly configured and working.",
                "model": API_SETTINGS["model_name"]
            }
        else:
            return {
                "status": "warning",
                "message": "Gemini API responded but with unexpected content.",
                "model": API_SETTINGS["model_name"]
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error connecting to Gemini API: {str(e)}",
            "model": API_SETTINGS["model_name"]
        }