import streamlit as st
from config import DOC_PROCESSING
from gemini_handler import get_medical_response

def extract_document_insights(store):
    """
    Extract key insights from document store
    
    Args:
        store: The vector store containing document chunks
        
    Returns:
        list: List of key insights extracted from the documents
    """
    if not store:
        return []
    
    # Get a sample of chunks to analyze
    sample_chunks = store.chunks[:DOC_PROCESSING['max_insights']] if len(store.chunks) > DOC_PROCESSING['max_insights'] else store.chunks
    
    # Use the AI to extract key insights
    insights = []
    for i, chunk in enumerate(sample_chunks):
        if i >= DOC_PROCESSING['max_insights']:  # Limit for efficiency
            break
        
        prompt = f"""
        Extract 1-2 key medical insights from this text:
        
        {chunk}
        
        Provide only the key medical insights in a concise format, focusing on diagnoses, 
        critical lab values, or notable medical findings.
        """
        
        response = get_medical_response(prompt)
        insights.append(response)
    
    return insights

def generate_medical_alerts(chunks):
    """
    Generate alerts for critical medical values in documents
    
    Args:
        chunks: List of document chunks
        
    Returns:
        list: List of medical alerts
    """
    if not chunks or len(chunks) == 0:
        return []
    
    # Critical medical values to watch for
    critical_terms = [
        "critical", "severe", "urgent", "emergency", "abnormal",
        "elevated", "dangerously", "immediately", "life-threatening"
    ]
    
    sample = chunks[0] if len(chunks) > 0 else ""
    
    # Generate alerts using AI
    prompt = f"""
    Analyze this medical document excerpt and identify any potential medical alerts 
    or critical values that healthcare providers should be aware of immediately.
    Focus only on urgent or critical findings that require attention.
    If there are no critical concerns, state "No critical medical alerts identified."
    
    Document excerpt:
    {sample[:800]}...
    
    Format your response as a bulleted list of alerts only.
    """
    
    response = get_medical_response(prompt)
    
    # Only return if actual alerts were found
    if "No critical medical alerts identified" not in response:
        return [response]
    return []

def generate_document_summary(chunk):
    """
    Generate a summary of a document chunk
    
    Args:
        chunk: Document chunk to summarize
        
    Returns:
        str: Summary of the document
    """
    if not chunk:
        return "No document content to summarize."
    
    # Generate a summary
    summary_prompt = f"""
    Generate a brief summary of this medical document in 2-3 sentences.
    Focus on the main medical condition and key findings.
    
    Document excerpt:
    {chunk[:800]}...
    """
    
    summary = get_medical_response(summary_prompt)
    return summary

def extract_lab_values(chunks):
    """
    Extract laboratory values from document chunks
    
    Args:
        chunks: List of document chunks
        
    Returns:
        dict: Dictionary of lab tests and their values
    """
    if not chunks or len(chunks) == 0:
        return {}
    
    sample = "\n\n".join(chunks[:2]) if len(chunks) > 1 else chunks[0]
    
    prompt = f"""
    Extract all laboratory test values from this medical document.
    Format your response as a simple list of "Test: Value" pairs.
    Include only objective laboratory measurements with their values and units.
    
    For example:
    - Hemoglobin: 14.2 g/dL
    - Glucose: 95 mg/dL
    
    Document excerpt:
    {sample[:1000]}...
    """
    
    response = get_medical_response(prompt)
    
    # Parse the response into a dictionary
    lab_values = {}
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            line = line[2:]  # Remove the bullet
        elif line.startswith('* '):
            line = line[2:]  # Remove the bullet
            
        if ':' in line:
            test, value = line.split(':', 1)
            lab_values[test.strip()] = value.strip()
    
    return lab_values

def extract_medications(chunks):
    """
    Extract medications from document chunks
    
    Args:
        chunks: List of document chunks
        
    Returns:
        list: List of medications with dosages if available
    """
    if not chunks or len(chunks) == 0:
        return []
    
    sample = "\n\n".join(chunks[:2]) if len(chunks) > 1 else chunks[0]
    
    prompt = f"""
    Extract all medications mentioned in this medical document.
    Include dosages, frequencies, and routes of administration if available.
    Format your response as a simple list of medications.
    
    For example:
    - Lisinopril 10mg daily
    - Metformin 500mg twice daily
    
    Document excerpt:
    {sample[:1000]}...
    """
    
    response = get_medical_response(prompt)
    
    # Parse the response into a list
    medications = []
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            medications.append(line[2:])  # Remove the bullet
        elif line.startswith('* '):
            medications.append(line[2:])  # Remove the bullet
        elif line and not line.startswith('#'):  # Ignore headings
            medications.append(line)
    
    return medications

def extract_diagnosis(chunks):
    """
    Extract diagnosis information from document chunks
    
    Args:
        chunks: List of document chunks
        
    Returns:
        list: List of diagnoses
    """
    if not chunks or len(chunks) == 0:
        return []
    
    sample = "\n\n".join(chunks[:2]) if len(chunks) > 1 else chunks[0]
    
    prompt = f"""
    Extract all diagnoses or medical conditions mentioned in this document.
    Format your response as a simple list of diagnoses.
    
    For example:
    - Type 2 Diabetes Mellitus
    - Essential Hypertension
    
    Document excerpt:
    {sample[:1000]}...
    """
    
    response = get_medical_response(prompt)
    
    # Parse the response into a list
    diagnoses = []
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            diagnoses.append(line[2:])  # Remove the bullet
        elif line.startswith('* '):
            diagnoses.append(line[2:])  # Remove the bullet
        elif line and not line.startswith('#'):  # Ignore headings
            diagnoses.append(line)
    
    return diagnoses

def analyze_document_section(chunks, section_type):
    """
    Analyze a specific section type in medical documents
    
    Args:
        chunks: List of document chunks
        section_type: Type of section to analyze (e.g., 'labs', 'medications', 'diagnosis')
        
    Returns:
        dict: Analysis results for the requested section
    """
    if section_type == 'labs':
        return {'lab_values': extract_lab_values(chunks)}
    elif section_type == 'medications':
        return {'medications': extract_medications(chunks)}
    elif section_type == 'diagnosis':
        return {'diagnoses': extract_diagnosis(chunks)}
    elif section_type == 'summary':
        return {'summary': generate_document_summary(chunks[0] if chunks else "")}
    else:
        return {'error': f"Unknown section type: {section_type}"}