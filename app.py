import streamlit as st
import os
from datetime import datetime

# Set page configuration - MUST BE FIRST COMMAND
st.set_page_config(
    page_title="MediAssist Pro",
    page_icon="🩺",
    layout="wide"
)

# Define component functions directly in app.py
def render_sidebar():
    """Render the sidebar content"""
    # API Key Settings
    with st.expander("🔑 API Settings", expanded=not st.session_state.api_key):
        api_status = check_api_status()
        
        if api_status["status"] == "success":
            st.success("✅ API connected successfully")
        else:
            st.warning(api_status["message"])
            
            # API Key input
            api_key = st.text_input(
                "Enter your Gemini API Key:",
                type="password",
                help="You can get a Gemini API key from https://makersuite.google.com/"
            )
            
            if api_key:
                st.session_state.api_key = api_key
                st.success("API key saved! Please test your connection.")
                
                if st.button("Test Connection"):
                    with st.spinner("Testing API connection..."):
                        # Force a refresh of the api status
                        updated_status = check_api_status()
                        if updated_status["status"] == "success":
                            st.success("✅ Connection successful!")
                        else:
                            st.error(f"⚠️ {updated_status['message']}")
    
    # Document Management Section
    st.markdown("### Document Management")
    
    # Document statistics
    if st.session_state.documents_processed:
        st.success("✅ Documents processed and ready")
        
        # Count PDF files in the documents folder
        pdf_count = len([f for f in os.listdir("documents") if f.endswith('.pdf')])
        
        st.markdown(f"""
        - **Documents uploaded:** {pdf_count} PDFs
        - **Knowledge chunks:** {len(st.session_state.vector_store.chunks) if st.session_state.vector_store else 0}
        """)
    else:
        st.info("📚 No documents processed yet")
    
    # Create a documents folder if it doesn't exist
    if not os.path.exists("documents"):
        os.makedirs("documents")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload medical PDFs", 
        type="pdf", 
        accept_multiple_files=True
    )
    
    # Save uploaded files
    if uploaded_files:
        for file in uploaded_files:
            file_path = os.path.join("documents", file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        
        st.success(f"{len(uploaded_files)} file(s) uploaded!")
    
    # Process documents button
    if st.button("Process Documents", type="primary"):
        # First check if API key is valid
        if not st.session_state.api_key:
            st.error("⚠️ Please add your Gemini API key in the API Settings section first.")
        else:
            with st.spinner("Processing documents..."):
                # Process all documents in the folder
                all_chunks = modules["process_documents"]("documents")
                
                if all_chunks:
                    # Create vector store
                    st.session_state.vector_store = modules["create_vector_store"](all_chunks)
                    st.session_state.documents_processed = True
                    st.session_state.extracted_insights = []  # Reset insights to generate new ones
                    st.success(f"Processed {len(all_chunks)} text chunks!")
                    
                    # Suggest switching to document tab
                    st.info("Documents processed! Now you can use the 'Medical Report Analysis' tab to ask questions about your documents.")
                else:
                    st.error("No text chunks extracted. Please check your documents.")
    
    # ADVANCED FEATURE: Document summarization
    if st.session_state.documents_processed:
        st.markdown("### Document Summary")
        if st.button("Generate Document Summary", type="secondary"):
            with st.spinner("Analyzing documents..."):
                # Get a representative chunk
                chunk = st.session_state.vector_store.chunks[0] if st.session_state.vector_store.chunks else ""
                summary = modules["generate_document_summary"](chunk)
                st.success("Summary generated!")
                st.info(summary)
    
    # Clear history buttons
    st.markdown("### Conversation Management")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clear General Chat", type="secondary") and st.session_state.general_chat_history:
            st.session_state.general_chat_history = []
            st.rerun()
    
    with col2:
        if st.button("Clear Report Chat", type="secondary") and st.session_state.report_chat_history:
            st.session_state.report_chat_history = []
            st.rerun()
    
    # ADVANCED FEATURE: Report Generation
    if st.session_state.documents_processed and (len(st.session_state.general_chat_history) > 0 or len(st.session_state.report_chat_history) > 0):
        st.markdown("### Advanced Tools")
        
        if st.button("Generate Clinical Summary Report", type="secondary"):
            with st.spinner("Creating clinical summary..."):
                # Use the utility function to generate a summary
                chat_history = st.session_state.report_chat_history if st.session_state.report_chat_history else st.session_state.general_chat_history
                report = modules["generate_clinical_summary"](st.session_state.vector_store, chat_history)
                st.success("Clinical summary generated!")
                st.info(report)
    
    # Medical Resources Section
    st.markdown("### Medical Resources")
    
    with st.expander("Trusted Health Sources"):
        st.markdown("""
        - [CDC - Centers for Disease Control](https://www.cdc.gov/)
        - [NIH - National Institutes of Health](https://www.nih.gov/)
        - [WHO - World Health Organization](https://www.who.int/)
        - [Mayo Clinic](https://www.mayoclinic.org/)
        - [MedlinePlus](https://medlineplus.gov/)
        """)
    
    # Help & Information
    with st.expander("Help & Information"):
        st.markdown("""
        ### Getting Started
        
        1. **Add your API Key**: Enter your Gemini API key in the API Settings section
        2. **Upload Documents**: Upload medical PDFs using the file uploader
        3. **Process Documents**: Click the Process Documents button
        4. **Ask Questions**: Use the tabs to ask medical questions or analyze documents
        
        ### API Key Information
        
        To use this application, you need a Google Gemini API key:
        
        1. Visit [Google AI Studio](https://makersuite.google.com/)
        2. Sign in or create a Google account
        3. Navigate to the API keys section
        4. Create a new API key
        5. Copy and paste it into the API Settings section
        """)
    
    # Footer
    st.markdown("---")
    st.caption(f"© 2025 MediAssist Pro | {datetime.now().strftime('%Y-%m-%d')}")
    st.caption("Powered by Gemini 2.0")

def render_about_page():
    """Render the About MediAssist Pro page content"""
    
    st.markdown("""
    <div class="welcome-container">
    <h3>ℹ️ About MediAssist Pro</h3>
    <p>MediAssist Pro is a specialized medical AI assistant designed for healthcare professionals, researchers, and patients.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Why MediAssist Pro is Different section
    st.markdown("""
    <div class="about-section">
    <h3>⭐ Why MediAssist Pro is Different</h3>
    <p>Unlike basic AI chatbots, our specialized medical document analyzer provides:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature grid using columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
        <span class="feature-icon">🔍</span><b>Medical Document Intelligence</b><br>
        Specialized algorithms extract insights from medical reports, lab results, and clinical notes.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
        <span class="feature-icon">⚠️</span><b>Critical Value Alerts</b><br>
        Automatically detects and flags potentially urgent medical findings in documents.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
        <span class="feature-icon">📋</span><b>Medical Notes & Annotations</b><br>
        Add your own observations and notes to document analysis for future reference.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
        <span class="feature-icon">📊</span><b>Healthcare Analytics</b><br>
        Track your medical research topics and document usage with detailed analytics.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
        <span class="feature-icon">📱</span><b>Multi-Platform Access</b><br>
        Access your medical AI assistant on desktop, tablet, or mobile with a responsive interface.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
        <span class="feature-icon">🔄</span><b>Export & Sharing</b><br>
        Export conversation history and insights for integration with other healthcare systems.
        </div>
        """, unsafe_allow_html=True)
    
    # Use Cases section
    st.markdown("""
    <div class="about-section">
    <h3>🏥 Use Cases</h3>
    </div>
    """, unsafe_allow_html=True)
    
    use_case_cols = st.columns(3)
    
    use_cases = [
        {
            "title": "Healthcare Providers",
            "icon": "👨‍⚕️",
            "description": "Quickly extract key insights from patient records, lab reports, and medical literature to support clinical decision-making."
        },
        {
            "title": "Researchers",
            "icon": "🔬",
            "description": "Analyze medical documents and research papers to identify patterns, extract data points, and accelerate literature reviews."
        },
        {
            "title": "Patients",
            "icon": "👤",
            "description": "Better understand medical reports, test results, and healthcare recommendations with plain-language explanations."
        }
    ]
    
    for i, use_case in enumerate(use_cases):
        with use_case_cols[i]:
            st.markdown(f"""
            <div class="feature-card">
            <h4>{use_case['icon']} {use_case['title']}</h4>
            <p>{use_case['description']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Advanced Features section
    st.markdown("""
    <div class="about-section">
    <h3>🔬 Advanced Features</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Tab-based explanation of advanced features
    feature_tabs = st.tabs([
        "🔍 Document Intelligence", 
        "⚠️ Medical Alerts", 
        "📊 Analytics & Insights",
        "📝 Notes & Annotations",
        "📋 Export & Sharing"
    ])
    
    with feature_tabs[0]:
        st.markdown("""
        ### Document Intelligence
        
        MediAssist Pro's document intelligence goes beyond simple text search:
        
        - **Semantic understanding** of medical terminology and contexts
        - **Automatic extraction** of key medical insights from documents
        - **Focused analysis** of specific sections like lab results, diagnoses, and treatments
        - **Correlation detection** between different medical findings
        - **Medical knowledge graph** connecting symptoms, conditions, and treatments
        
        This allows healthcare professionals to quickly get answers to complex questions about patient records, lab results, and clinical notes.
        """)
    
    with feature_tabs[1]:
        st.markdown("""
        ### Medical Alerts System
        
        The medical alerts system automatically detects potentially critical values in documents:
        
        - **Critical lab value detection** for out-of-range results
        - **Urgent finding highlighting** to call attention to important diagnostic information
        - **Risk factor identification** across multiple documents
        - **Medication interaction warnings** based on document content
        - **Follow-up reminders** for time-sensitive medical issues
        
        These alerts help ensure that important medical information isn't overlooked during document review.
        """)
    
    with feature_tabs[2]:
        st.markdown("""
        ### Analytics & Insights
        
        Comprehensive analytics provide valuable insights into medical information usage:
        
        - **Topic tracking** to identify frequently researched medical areas
        - **Usage patterns** showing document analysis vs. general medical queries
        - **Session analytics** to track research over time
        - **Custom dashboards** for visualizing healthcare information trends
        - **Insight extraction** to surface patterns across multiple documents
        
        These analytics help users identify knowledge gaps and track their medical research interests over time.
        """)
    
    with feature_tabs[3]:
        st.markdown("""
        ### Notes & Annotations
        
        The notes and annotations system enhances document analysis with personal insights:
        
        - **Timestamped notes** to record observations during document review
        - **Context linking** of notes to specific document sections
        - **Collaborative annotations** for team-based document analysis
        - **Color-coded categorization** for different types of medical notes
        - **Follow-up flagging** for items requiring additional attention
        
        This feature helps users maintain a personal record of thoughts and observations while reviewing medical documents.
        """)
    
    with feature_tabs[4]:
        st.markdown("""
        ### Export & Sharing
        
        Export capabilities make it easy to integrate insights with other systems:
        
        - **Markdown export** of complete conversation history
        - **PDF reporting** for formal documentation
        - **Integration APIs** for connecting with electronic health record systems
        - **Secure sharing** of insights with healthcare team members
        - **Structured data export** for further analysis in other tools
        
        These export features help bridge the gap between AI-assisted analysis and existing healthcare workflows.
        """)
    
    # Technology section
    st.markdown("""
    <div class="about-section">
    <h3>🔧 Technology</h3>
    <p>MediAssist Pro is built on advanced AI technology specifically designed for medical applications:</p>
    </div>
    """, unsafe_allow_html=True)
    
    tech_cols = st.columns(2)
    
    with tech_cols[0]:
        st.markdown("""
        - **Google Gemini 2.0** AI foundation model
        - **Natural Language Processing** for medical terminology understanding
        - **Document-aware context processing**
        - **Medical knowledge graph integration**
        """)
    
    with tech_cols[1]:
        st.markdown("""
        - **Secure document handling**
        - **Analytics and visualization engine**
        - **Multi-document correlation analysis**
        - **Responsive and accessible user interface**
        """)

def check_api_status():
    """Wrapper for the gemini_handler.check_api_status function"""
    from gemini_handler import check_api_status
    return check_api_status()

# Set up caching for imported modules to improve performance
@st.cache_resource
def import_modules():
    """Import all required modules and return them as a dictionary"""
    import matplotlib.pyplot as plt
    import pandas as pd
    from config import init_session_state
    from styles import load_css
    from utils import track_interaction, export_to_markdown, generate_clinical_summary
    from document_processor import process_documents
    from vector_store import create_vector_store, find_relevant_chunks
    from gemini_handler import get_medical_response
    from document_analysis import extract_document_insights, generate_medical_alerts, generate_document_summary
    from analytics import generate_analytics
    
    return {
        "plt": plt,
        "pd": pd,
        "init_session_state": init_session_state,
        "load_css": load_css,
        "track_interaction": track_interaction,
        "export_to_markdown": export_to_markdown,
        "process_documents": process_documents,
        "create_vector_store": create_vector_store,
        "find_relevant_chunks": find_relevant_chunks,
        "get_medical_response": get_medical_response,
        "extract_document_insights": extract_document_insights,
        "generate_medical_alerts": generate_medical_alerts,
        "generate_analytics": generate_analytics,
        "generate_document_summary": generate_document_summary,
        "generate_clinical_summary": generate_clinical_summary
    }

# Import all modules at once
modules = import_modules()

# Load CSS
modules["load_css"]()

# Initialize session state
modules["init_session_state"]()

# App title at the very top
st.title("🩺 MediAssist Pro: Medical Document Intelligence")

# Define the tabs
tabs = st.tabs(["📋 General Medical", "🔍 Medical Report Analysis", "📊 Analytics", "ℹ️ About MediAssist Pro"])

with tabs[0]:  # General Queries Tab
    st.session_state.active_tab = "General"
    
    # 1. Welcome message
    st.markdown("""
    <div class="welcome-container">
    <h3>👋 Welcome to MediAssist Pro</h3>
    <p>Ask any general medical questions about conditions, treatments, symptoms, or health information.</p>
    <p>For document-specific analysis, please use the "Medical Report Analysis" tab.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Starter prompts (only show if no conversation history)
    if not st.session_state.general_chat_history:
        st.markdown("### Suggested Topics:")
        
        col1, col2, col3 = st.columns(3)
        
        prompts_columns = [col1, col2, col3]
        starter_prompts = [
            "Common symptoms of type 2 diabetes",
            "High blood pressure effects on the heart",
            "Recommended screening tests for adults over 50",
            "How antibiotics work and when to use them",
            "Lifestyle changes to prevent heart disease",
            "Difference between Alzheimer's and dementia"
        ]
        
        for i, prompt in enumerate(starter_prompts):
            with prompts_columns[i % 3]:
                if st.button(f"🔍 {prompt}", key=f"g_prompt_{i}", use_container_width=True, type="secondary"):
                    with st.spinner("Generating response..."):
                        response = modules["get_medical_response"](prompt)
                        # Add to general chat history
                        st.session_state.general_chat_history.append({"query": prompt, "response": response})
                        # Track interaction
                        modules["track_interaction"](prompt, response, "General")
                        st.rerun()
    
    # 3. Query input
    st.markdown('<div class="chat-input-section">', unsafe_allow_html=True)
    
    g_col1, g_col2 = st.columns([5, 1])
    
    with g_col1:
        general_query = st.text_input(
            "Enter your health-related question:", 
            key="general_question_input", 
            value="",
            placeholder="Example: What are the symptoms of diabetes?"
        )
    
    with g_col2:
        general_submit = st.button("Ask", key="general_submit", use_container_width=True, type="primary")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process general query
    if general_submit and general_query.strip():
        with st.spinner("Generating response..."):
            # Generate response without document context for general queries
            response = modules["get_medical_response"](general_query)
            
            # Add to general chat history
            st.session_state.general_chat_history.append({"query": general_query, "response": response})
            
            # Track interaction
            modules["track_interaction"](general_query, response, "General")
            
            # Force a rerun to update the UI
            st.rerun()
    
    # 4. Display chat conversation
    if st.session_state.general_chat_history:
        st.markdown("### Conversation")
        
        # Display chat history (proper order with most recent at bottom)
        for exchange in st.session_state.general_chat_history:
            with st.chat_message("user"):
                st.write(exchange["query"])
            with st.chat_message("assistant", avatar="🩺"):
                st.write(exchange["response"])
    
    # Compact disclaimer
    st.markdown("""
    <div class="disclaimer">
    <strong>Disclaimer:</strong> This AI assistant is not a substitute for professional medical advice, diagnosis, or treatment.
    </div>
    """, unsafe_allow_html=True)

with tabs[1]:  # Report Analysis Tab
    st.session_state.active_tab = "Report"
    
    # 1. Welcome message
    if st.session_state.documents_processed:
        st.markdown("""
        <div class="welcome-container">
        <h3>📄 Medical Report Intelligence</h3>
        <p>Ask specific questions about the medical reports you've uploaded and processed.</p>
        <p>The AI will analyze your documents to provide targeted answers based on their content.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ADVANCED FEATURE: Medical alerts from document content
        if st.session_state.vector_store and st.session_state.vector_store.chunks:
            alerts = modules["generate_medical_alerts"](st.session_state.vector_store.chunks)
            if alerts:
                st.error("⚠️ **MEDICAL ALERTS DETECTED**")
                for alert in alerts:
                    st.warning(alert)
        
        # Run document insights extraction if needed
        if not st.session_state.extracted_insights and st.session_state.vector_store:
            st.session_state.extracted_insights = modules["extract_document_insights"](st.session_state.vector_store)
        
        # Display document insights
        if st.session_state.extracted_insights:
            st.markdown("### 🔍 Key Document Insights")
            for i, insight in enumerate(st.session_state.extracted_insights):
                st.info(insight)
    else:
        st.warning("⚠️ No documents have been processed yet. Please upload and process medical documents in the sidebar first.")
    
    # 2. Starter suggestions for document questions
    if st.session_state.documents_processed and not st.session_state.report_chat_history:
        st.markdown("### Suggested Document Questions:")
        
        example_cols = st.columns(3)
        doc_prompts = [
            "What is the patient's diagnosis?",
            "Summarize the key lab results",
            "What medications is the patient taking?",
            "What treatment plan is recommended?",
            "Are there any abnormal vital signs?",
            "What are the patient's risk factors?"
        ]
        
        for i, prompt in enumerate(doc_prompts):
            with example_cols[i % 3]:
                if st.button(f"🔍 {prompt}", key=f"d_prompt_{i}", use_container_width=True, type="secondary"):
                    with st.spinner("Analyzing documents..."):
                        # Find relevant context from documents
                        relevant_chunks = modules["find_relevant_chunks"](st.session_state.vector_store, prompt)
                        context = "\n\n".join(relevant_chunks)
                        
                        # Generate response with document context
                        response = modules["get_medical_response"](prompt, context)
                        
                        # Add to report chat history
                        st.session_state.report_chat_history.append({"query": prompt, "response": response})
                        
                        # Track interaction
                        modules["track_interaction"](prompt, response, "Report")
                        
                        st.rerun()
    
    # 3. Query input for report tab
    if st.session_state.documents_processed:
        st.markdown('<div class="chat-input-section">', unsafe_allow_html=True)
        
        r_col1, r_col2 = st.columns([5, 1])
        
        with r_col1:
            report_query = st.text_input(
                "Enter your question about the medical reports:", 
                key="report_question_input", 
                value="",
                placeholder="Example: What is the patient's HbA1c level?"
            )
        
        with r_col2:
            report_submit = st.button("Ask", key="report_submit", use_container_width=True, type="primary")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Process report query
    if st.session_state.documents_processed and report_submit and report_query.strip():
        with st.spinner("Analyzing medical reports..."):
            # Find relevant context from documents
            relevant_chunks = modules["find_relevant_chunks"](st.session_state.vector_store, report_query)
            context = "\n\n".join(relevant_chunks)
            
            # Generate response with document context
            response = modules["get_medical_response"](report_query, context)
            
            # Add to report chat history
            st.session_state.report_chat_history.append({"query": report_query, "response": response})
            
            # Track interaction
            modules["track_interaction"](report_query, response, "Report")
            
            # Force a rerun to update the UI
            st.rerun()
    
    # 4. Display report chat conversation
    if st.session_state.report_chat_history:
        st.markdown("### Document Analysis")
        
        # Display chat history
        for exchange in st.session_state.report_chat_history:
            with st.chat_message("user"):
                st.write(exchange["query"])
            with st.chat_message("assistant", avatar="🩺"):
                st.write(exchange["response"])
    
    # ADVANCED FEATURE: Medical notes and annotations
    if st.session_state.documents_processed:
        with st.expander("📝 Medical Notes & Annotations"):
            note_text = st.text_area("Add a medical note or observation", key="medical_note_input")
            note_col1, note_col2 = st.columns([1, 4])
            
            with note_col1:
                if st.button("Add Note", use_container_width=True):
                    if note_text.strip():
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.session_state.medical_notes.append({
                            "timestamp": timestamp,
                            "text": note_text
                        })
                        st.rerun()
            
            if st.session_state.medical_notes:
                st.markdown("### Your Medical Notes")
                for note in st.session_state.medical_notes:
                    st.markdown(f"**{note['timestamp']}**: {note['text']}")
    
    # Compact disclaimer
    st.markdown("""
    <div class="disclaimer">
    <strong>Disclaimer:</strong> This AI assistant is not a substitute for professional medical advice, diagnosis, or treatment.
    </div>
    """, unsafe_allow_html=True)

with tabs[2]:  # Analytics Tab
    # Get analytics data
    analytics_data = modules["generate_analytics"]()
    
    st.markdown("""
    <div class="welcome-container">
    <h3>📊 Usage Analytics & Insights</h3>
    <p>Track your interactions and gain insights from your medical queries.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Usage statistics
    total_interactions = st.session_state.analytics['general_interactions'] + st.session_state.analytics['document_interactions']
    
    if total_interactions > 0:
        st.markdown("### Usage Summary")
        
        # Create metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Interactions", total_interactions)
        with col2:
            st.metric("General Queries", st.session_state.analytics['general_interactions'])
        with col3:
            st.metric("Document Analyses", st.session_state.analytics['document_interactions'])
        
        # Only display the chart if there's data
        if sum([st.session_state.analytics['general_interactions'], st.session_state.analytics['document_interactions']]) > 0:
            # Use the cached matplotlib
            plt = modules["plt"]
            
            # Create visualization of interaction types
            st.markdown("### Query Distribution")
            
            fig, ax = plt.subplots(figsize=(6, 4))
            data = [st.session_state.analytics['general_interactions'], 
                   st.session_state.analytics['document_interactions']]
            labels = ['General Medical', 'Document Analysis']
            colors = ['#2e7d32', '#1976D2']
            
            ax.pie(data, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
        
        # Popular topics
        if analytics_data['common_topics']:
            st.markdown("### Common Topics")
            st.dataframe(analytics_data['topics_df'], hide_index=True, use_container_width=True)
        
        # ADVANCED FEATURE: Export conversation history
        st.markdown("### 📋 Export Conversation History")
        export_col1, export_col2 = st.columns([1, 3])
        
        with export_col1:
            if st.button("Export to Markdown", use_container_width=True):
                markdown_text = modules["export_to_markdown"]()
                st.download_button(
                    label="Download Markdown",
                    data=markdown_text,
                    file_name=f"mediassist_export_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown"
                )
    else:
        st.info("Start interacting with the chatbot to generate analytics.")

with tabs[3]:  # About MediAssist Pro Tab
    # Use local function to render about page
    render_about_page()

# Sidebar for document management and other tools
with st.sidebar:
    # Use local function to render sidebar
    render_sidebar()