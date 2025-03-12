MediAssist Pro is an AI-powered medical document intelligence platform that helps healthcare professionals, researchers, and patients analyze and extract insights from medical documents. Using Google's Gemini 2.0 AI model, it provides accurate responses to health-related queries and performs in-depth analysis of uploaded medical documents.
Features

📋 General Medical Queries: Ask any health-related questions and receive accurate, helpful responses
🔍 Document Analysis: Upload and analyze medical reports, lab results, and clinical notes
⚠️ Critical Value Alerts: Automatically identifies potentially urgent medical findings in documents
🧠 Automatic Insights: Extracts key medical insights from documents without manual review
📊 Analytics Dashboard: Track and visualize your medical research patterns and interests
📝 Medical Notes: Add personal annotations and observations to document analysis
📤 Export Functionality: Export conversation history and insights for reference

Getting Started
Prerequisites

Python 3.8+
Streamlit
Google Generative AI package
Other dependencies in requirements.txt

Installation

Clone the repository:
Copygit clone https://github.com/chandrujobs/MediAssist-Pro.git
cd MediAssist-Pro

Create a virtual environment:
Copypython -m venv medbot_env

Activate the virtual environment:

Windows:
Copymedbot_env\Scripts\activate

macOS/Linux:
Copysource medbot_env/bin/activate



Install required packages:
Copypip install -r requirements.txt

Set up your Gemini API key:

Get an API key from Google AI Studio
You'll enter this key in the app interface when prompted


Run the application:
Copystreamlit run app.py


Usage

General Medical Queries:

Navigate to the "General Medical" tab
Ask any health-related question
Get accurate, helpful responses based on medical knowledge


Document Analysis:

Upload medical PDFs using the sidebar
Click "Process Documents" to analyze them
Navigate to the "Medical Report Analysis" tab
Ask specific questions about the documents
View automatically extracted insights and alerts


Analytics:

Navigate to the "Analytics" tab
View usage statistics and common topics
Export conversation history



Project Structure
CopyMediAssist-Pro/
├── app.py                   # Main application file
├── config.py                # Configuration settings
├── styles.py                # CSS styling
├── utils.py                 # Utility functions
├── analytics.py             # Analytics functions
├── gemini_handler.py        # Gemini API integration
├── document_processor.py    # Document processing functions
├── document_analysis.py     # Document analysis functions
├── vector_store.py          # Vector storage for semantic search
├── requirements.txt         # Package dependencies
└── documents/               # Folder for uploaded documents
Use Cases

Healthcare Providers: Extract key insights from patient records and medical literature
Researchers: Analyze medical documents and research papers to identify patterns
Patients: Better understand medical reports and healthcare recommendations

Limitations

Document processing is limited to PDFs
Larger documents may take longer to process
Requires a Google Gemini API key
Not intended for diagnostic or treatment decisions

Disclaimer
This AI assistant is not a substitute for professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider for medical concerns.
License
This project is licensed under the MIT License - see the LICENSE file for details.
Acknowledgments

Google Gemini API for AI capabilities
Streamlit for the web interface framework
PyPDF for PDF processing

Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
