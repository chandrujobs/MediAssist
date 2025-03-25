import os
import time
import requests
import json
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components

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
    margin-bottom: 3rem;
    box-shadow: 0 0 20px rgba(0,0,0,0.05);
    width: 100%;
    overflow: auto;
    min-height: 500px;
}
.diagram-wrapper {
    margin-bottom: 50px;
    padding-bottom: 30px;
    border-bottom: 1px solid #eaeaea;
}
.code-section {
    margin-top: 50px;
    padding-top: 20px;
}
textarea {
    border-radius: 12px !important;
}
.download-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin: 1rem auto;
    padding: 12px 24px;
    background: #FF8C00; /* Orange color */
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    transition: all 0.2s ease;
}
.download-button:hover {
    background: #E67E00; /* Darker orange on hover */
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    transform: translateY(-1px);
}
.download-button:active {
    transform: translateY(1px);
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 VisiFlow: Architecture Diagram Studio")
st.markdown("Design, visualize, and refine system architecture with the power of AI-generated diagrams.")

# Sidebar layout - Color customization with spacer technique
st.sidebar.header("🎨 Customize Component Colors")

# Initialize color settings in session state if they don't exist
if 'db_color' not in st.session_state:
    st.session_state.db_color = "#F94144"
if 'api_color' not in st.session_state:
    st.session_state.api_color = "#F3722C"
if 'svc_color' not in st.session_state:
    st.session_state.svc_color = "#43AA8B"
if 'user_color' not in st.session_state:
    st.session_state.user_color = "#577590"
if 'storage_color' not in st.session_state:
    st.session_state.storage_color = "#F9C74F"
if 'msg_color' not in st.session_state:
    st.session_state.msg_color = "#9F86C0"

# Simple approach - individual color pickers with descriptive labels
st.sidebar.color_picker("Database", st.session_state.db_color, key="db_color")
st.sidebar.color_picker("API Gateway", st.session_state.api_color, key="api_color")
st.sidebar.color_picker("Services", st.session_state.svc_color, key="svc_color")
st.sidebar.color_picker("User", st.session_state.user_color, key="user_color")
st.sidebar.color_picker("Storage", st.session_state.storage_color, key="storage_color")
st.sidebar.color_picker("Messaging", st.session_state.msg_color, key="msg_color")

# Collect color settings from session state
color_settings = {
    "Database": st.session_state.db_color,
    "API Gateway": st.session_state.api_color,
    "Services": st.session_state.svc_color,
    "User": st.session_state.user_color,
    "Storage": st.session_state.storage_color,
    "Messaging": st.session_state.msg_color
}

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

# Generate a unique key for the file uploader to force reset
if 'file_uploader_key' not in st.session_state:
    st.session_state['file_uploader_key'] = '0'
    
# Requirement upload
st.sidebar.header("📄 Upload Requirement Document")
requirement_file = st.sidebar.file_uploader("Upload a .txt or .docx file", 
                                            type=["txt", "docx"],
                                            key=st.session_state['file_uploader_key'])
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

# Reset logic - clear template, prompt, and file uploader too
if reset:
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
        
    # Force clear file uploader by using a new key
    st.session_state['file_uploader_key'] = str(hash(str(time.time())))
    
    # Rerun to take effect
    st.rerun()

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
            
            # Create color suggestions from the color picker values
            color_comment = "\n".join([f"Use color {color} for {component}" for component, color in color_settings.items()])
            
            # Create full prompt with color suggestions
            full_prompt = final_prompt + "\n\n" + color_comment + "\n\nEnsure the diagram syntax is fully compatible with Mermaid version 9.4.3 (NOT 11.5.0). Use only simple flowchart format (flowchart TD or LR) to avoid syntax errors."
            
            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert system designer. Based on the user's prompt or uploaded requirements, "
                            "generate a valid and compatible mermaid.js diagram using Mermaid version 9.4.3 syntax (NOT 11.5.0). "
                            "IMPORTANT: Use only simple flowchart format (flowchart TD or LR) to avoid syntax errors. "
                            "Use the color hints provided by the user for different component types. "
                            "Ensure it visually represents the architecture clearly. "
                            "Do not use advanced Mermaid features that may cause compatibility issues."
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
    
    # Improved download button function with better error handling
    download_js = """
    <script>
    // Wait for mermaid to render before setting up the download
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            setupDownloadButton();
        }, 1000); // Give mermaid time to render
    });
    
    function     setupDownloadButton() {
        const downloadBtn = document.getElementById('download-png-btn');
        if (downloadBtn) {
            // Use addEventListener instead of inline onclick
            downloadBtn.addEventListener('click', function() {
                downloadPNG();
            });
        }
    }
    
    // Function to create a PNG from the SVG and trigger download
    function downloadPNG() {
        // Change button state
        const btn = document.getElementById('download-png-btn');
        if (!btn) return;
        
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite;margin-right:8px;">↻</span> Processing...';
        btn.disabled = true;
        btn.style.opacity = '0.7';
        
        try {
            // Get the SVG element
            const svg = document.querySelector('#mermaid-diagram svg');
            if (!svg) {
                throw new Error('No diagram found');
            }
            
            // Get dimensions
            const svgWidth = parseInt(svg.getAttribute('width') || svg.getBoundingClientRect().width);
            const svgHeight = parseInt(svg.getAttribute('height') || svg.getBoundingClientRect().height);
            
            // Create a canvas with 2x resolution for better quality
            const canvas = document.createElement('canvas');
            const scale = 2; // Scale for higher resolution
            canvas.width = svgWidth * scale;
            canvas.height = svgHeight * scale;
            
            // Get canvas context and scale it
            const ctx = canvas.getContext('2d');
            ctx.scale(scale, scale);
            
            // Create a proper SVG blob with XML declaration and correct dimensions
            const svgData = new XMLSerializer().serializeToString(svg);
            const svgBlob = new Blob([
                '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n',
                '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n',
                svgData
            ], {type: 'image/svg+xml'});
            
            const url = URL.createObjectURL(svgBlob);
            
            // Create image and draw to canvas when loaded
            const img = new Image();
            
            img.onload = function() {
                // Fill with white background
                ctx.fillStyle = '#FFFFFF';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Draw the SVG image
                ctx.drawImage(img, 0, 0, svgWidth, svgHeight);
                
                // Convert to PNG
                try {
                    // Use toBlob for better browser compatibility
                    canvas.toBlob(function(blob) {
                        // Create download link
                        const downloadUrl = URL.createObjectURL(blob);
                        const downloadLink = document.createElement('a');
                        downloadLink.href = downloadUrl;
                        downloadLink.download = 'architecture_diagram.png';
                        
                        // Append to body, click and remove
                        document.body.appendChild(downloadLink);
                        downloadLink.click();
                        document.body.removeChild(downloadLink);
                        
                        // Cleanup
                        URL.revokeObjectURL(downloadUrl);
                        URL.revokeObjectURL(url);
                        
                        // Restore button
                        btn.innerHTML = originalHTML;
                        btn.disabled = false;
                        btn.style.opacity = '1';
                    }, 'image/png', 1.0);
                } catch (e) {
                    // Fallback to older method if toBlob fails
                    try {
                        const dataUrl = canvas.toDataURL('image/png');
                        const downloadLink = document.createElement('a');
                        downloadLink.href = dataUrl;
                        downloadLink.download = 'architecture_diagram.png';
                        document.body.appendChild(downloadLink);
                        downloadLink.click();
                        document.body.removeChild(downloadLink);
                        
                        // Restore button
                        btn.innerHTML = originalHTML;
                        btn.disabled = false;
                        btn.style.opacity = '1';
                    } catch (err) {
                        alert('Failed to generate PNG: ' + err.message);
                        console.error(err);
                        btn.innerHTML = originalHTML;
                        btn.style.pointerEvents = 'auto';
                        btn.style.opacity = '1';
                    }
                }
            };
            
            img.onerror = function() {
                alert('Failed to load the diagram image. Please try again.');
                console.error('Image loading failed');
                btn.innerHTML = originalHTML;
                btn.disabled = false;
                btn.style.opacity = '1';
            };
            
            // Load the image
            img.src = url;
            
        } catch (error) {
            alert('Failed to download: ' + error.message);
            console.error('Download failed:', error);
            btn.innerHTML = originalHTML;
            btn.disabled = false;
            btn.style.opacity = '1';
        }
    }
    
    // Add spin animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    </script>
    """
    
    mermaid_html = f"""
    {download_js}
    <div class="diagram-wrapper">
        <div class='mermaid-container'>
            <div class="mermaid" id="mermaid-diagram">
                {st.session_state.mermaid_code}
            </div>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@9.4.3/dist/mermaid.min.js"></script>
            <script>
                mermaid.initialize({{
                    startOnLoad: true,
                    theme: 'default',
                    securityLevel: 'loose',
                    flowchart: {{
                        useMaxWidth: true,
                        htmlLabels: true,
                        curve: 'basis'
                    }}
                }});
            </script>
        </div>
        
            <div style="text-align: center; margin-top: 20px;">
                <button id="download-png-btn" class="download-button">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style="margin-right: 8px;">
                        <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                        <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                    </svg>
                    Download Diagram
                </button>
            </div>
    </div>
    """
    
    components.html(mermaid_html, height=800, scrolling=True)
    
    # Use expander for code and explanation to save space
    st.markdown('<div class="code-section"></div>', unsafe_allow_html=True)
    with st.expander("🧬 View & Edit Mermaid Code", expanded=False):
        edited_code = st.text_area(
            "You can refine the diagram by editing the code below:",
            value=st.session_state.mermaid_code,
            height=300
        )
        
        if st.button("🔄 Re-render Updated Diagram"):
            st.session_state.mermaid_code = edited_code
            st.rerun()
    
    with st.expander("🧠 View Explanation"):
        st.markdown(st.session_state.explanation or "No explanation provided.")
