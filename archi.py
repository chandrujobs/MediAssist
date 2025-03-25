import os
import requests
import json
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from io import BytesIO
import base64

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_id = os.getenv("MODEL_ID")

# Initialize session state for managing app state
if 'diagram_generated' not in st.session_state:
    st.session_state.diagram_generated = False
if 'mermaid_code' not in st.session_state:
    st.session_state.mermaid_code = ""
if 'explanation' not in st.session_state:
    st.session_state.explanation = ""

# Streamlit page config
st.set_page_config(
    page_title="VisiFlow - Architecture Diagram Studio",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
.main-container {
    padding: 2rem;
}
.mermaid-container {
    background-color: #ffffff;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 0 20px rgba(0,0,0,0.05);
    width: 100%;
    overflow: auto;
}
textarea {
    border-radius: 12px !important;
}
.color-row {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    width: 100%;
}
.color-col {
    display: flex;
    flex-direction: column;
    flex: 0 0 33.333333%;
    max-width: 33.333333%;
    padding: 0 5px;
    margin-bottom: 10px;
}
.download-btn {
    margin-top: 1rem;
    margin-bottom: 2rem;
}
.stExpander {
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 VisiFlow: Architecture Diagram Studio")
st.markdown("Design, visualize, and refine system architecture with the power of AI-generated diagrams.")

# Sidebar layout
st.sidebar.header("🎨 Customize Component Colors")

# 2 rows x 3 columns layout for color pickers
color_labels = ["Database", "API Gateway", "Services", "User", "Storage", "Messaging"]
color_defaults = ["#F94144", "#F3722C", "#43AA8B", "#577590", "#F9C74F", "#9F86C0"]
color_settings = {}

# Create 2 rows with 3 columns each
st.sidebar.markdown("<div class='color-row'>", unsafe_allow_html=True)
for i in range(3):  # First row
    st.sidebar.markdown(f"<div class='color-col'>", unsafe_allow_html=True)
    color_settings[color_labels[i]] = st.sidebar.color_picker(
        color_labels[i], color_defaults[i], key=f"color_{i}"
    )
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.markdown("<div class='color-row'>", unsafe_allow_html=True)
for i in range(3, 6):  # Second row
    st.sidebar.markdown(f"<div class='color-col'>", unsafe_allow_html=True)
    color_settings[color_labels[i]] = st.sidebar.color_picker(
        color_labels[i], color_defaults[i], key=f"color_{i}"
    )
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Prompt templates
st.sidebar.header("📋 Prompt Templates")
template_options = [
    "E-commerce system with user login, product catalog, cart, and payment",
    "IoT architecture with edge devices, gateway, cloud processing, and dashboard",
    "Data lakehouse on Azure with ingestion, processing, and analytics",
    "Event-driven microservices using Kafka and REST APIs",
    "Multi-cloud deployment with GCP, AWS, and Azure integration"
]
selected_template = st.sidebar.selectbox(
    "Choose a template to autofill:",
    ["-- Select a Template --"] + template_options
)

# Requirement upload
st.sidebar.header("📄 Upload Requirement Document")
requirement_file = st.sidebar.file_uploader("Upload a .txt or .docx file", type=["txt", "docx"])
requirement_text = ""
if requirement_file:
    file_ext = requirement_file.name.split(".")[-1]
    if file_ext == "txt":
        requirement_text = requirement_file.read().decode("utf-8")
    elif file_ext == "docx":
        try:
            import docx
            doc = docx.Document(requirement_file)
            requirement_text = "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            st.error("Missing dependency for .docx files. Run: pip install python-docx")

# Generate buttons
sidebar_generate = st.sidebar.button("✨ Generate from Requirement")
reset = st.sidebar.button("🔄 Reset All")

# Reset logic
if reset:
    for key in st.session_state.keys():
        del st.session_state[key]
    st.experimental_rerun()

# Prompt area (template + text input)
prompt = ""
if not requirement_text:
    if selected_template and selected_template != "-- Select a Template --":
        prompt = selected_template
    prompt = st.text_area("🔧 Describe your system architecture:", value=prompt, height=150)
    generate = st.button("✨ Generate Diagram")
else:
    st.info(f"Using uploaded requirement document: {requirement_file.name}")
    generate = False  # Don't show the regular generate button when using requirement file

# Ensure only one trigger works
trigger = False
final_prompt = ""

if requirement_text and sidebar_generate:
    trigger = True
    final_prompt = requirement_text
elif not requirement_text and generate:
    trigger = True
    final_prompt = prompt

if trigger:
    if not final_prompt:
        st.warning("Please provide a system description or upload a requirement document.")
    else:
        with st.spinner("Generating architecture diagram..."):
            endpoint = f"{base_url}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            color_comment = "\n".join([f"Use color {color} for {label}" for label, color in color_settings.items()])
            full_prompt = final_prompt + "\n\n" + color_comment + "\n\nEnsure the diagram syntax is fully compatible with Mermaid version 11.5.0. Use simple flowchart format if unsure."
            
            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert system designer. Based on the user's prompt or uploaded requirements, "
                            "generate a valid and compatible mermaid.js diagram using Mermaid version 11.5.0 syntax. "
                            "Ensure it visually represents the architecture clearly and use styling based on user-provided color hints."
                        )
                    },
                    {"role": "user", "content": full_prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 700
            }
            
            response = requests.post(endpoint, headers=headers, json=payload)
            result = response.json()
            
            if response.status_code == 200:
                output = result["choices"][0]["message"]["content"]
                if "```mermaid" in output:
                    mermaid_code = output.split("```mermaid")[1].split("```")[0].strip()
                    explanation = output.replace(f"```mermaid\n{mermaid_code}\n```", "").strip()
                    
                    # Save to session state
                    st.session_state.diagram_generated = True
                    st.session_state.mermaid_code = mermaid_code
                    st.session_state.explanation = explanation
                else:
                    st.error("Diagram not found or invalid syntax. Please refine your prompt or check Mermaid compatibility.")
            else:
                st.error(f"Error {response.status_code}: {result}")

# Display diagram if generated
if st.session_state.diagram_generated:
    st.markdown("### 🖼️ Generated Architecture Diagram")
    
    # Add download button function for PNG export
    download_js = """
    <script>
    function downloadDiagram() {
        const svg = document.querySelector("#mermaid-diagram svg");
        if (!svg) {
            alert("No diagram found to download");
            return;
        }
        
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const data = (new XMLSerializer()).serializeToString(svg);
        const DOMURL = window.URL || window.webkitURL || window;
        
        const img = new Image();
        const svgBlob = new Blob([data], {type: "image/svg+xml;charset=utf-8"});
        const url = DOMURL.createObjectURL(svgBlob);
        
        img.onload = function() {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            DOMURL.revokeObjectURL(url);
            
            const pngUrl = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
            const downloadLink = document.createElement("a");
            downloadLink.href = pngUrl;
            downloadLink.download = "architecture_diagram.png";
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        };
        img.src = url;
    }
    </script>
    """
    
    mermaid_html = f"""
    {download_js}
    <div class='mermaid-container'>
        <div class="mermaid" id="mermaid-diagram">
            {st.session_state.mermaid_code}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@11.5.0/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad:true}});</script>
        <button onclick="downloadDiagram()" class="download-btn">📥 Download as PNG</button>
    </div>
    """
    
    components.html(mermaid_html, height=600)
    
    # Use expander for code and explanation to save space
    with st.expander("🧬 View Mermaid Code"):
        edited_code = st.text_area(
            "You can refine the diagram by editing the code below:",
            value=st.session_state.mermaid_code,
            height=300
        )
        
        if st.button("🔄 Re-render Updated Diagram"):
            st.session_state.mermaid_code = edited_code
            st.experimental_rerun()
    
    with st.expander("🧠 View Explanation"):
        st.markdown(st.session_state.explanation or "No explanation provided.")
