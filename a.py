import streamlit as st
try:
    import fitz  # PyMuPDF
except ImportError:
    try:
        import pymupdf as fitz
    except ImportError:
        st.error("PyMuPDF is not installed correctly. Please install with 'pip install pymupdf'")
        st.stop()

import pandas as pd
import os
from io import BytesIO
import base64
import time
import shutil
import zipfile
import numpy as np
from PIL import Image
import io

def detect_and_remove_logos(page, min_size=100, max_size=10000, logo_detection_threshold=0.5):
    """
    Detects and removes potential logos from a PDF page with improved detection.
    """
    log_entries = []
    
    try:
        # Existing logo detection implementation
        img_list = page.get_images(full=True)
        
        if not img_list:
            return []  # No images on this page
            
        for img_index, img_info in enumerate(img_list):
            xref = img_info[0]  # Get the image reference
            
            try:
                # Get image properties
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Open the image with PIL
                pil_image = Image.open(io.BytesIO(image_bytes))
                width, height = pil_image.size
                img_size = width * height
                
                # Convert to grayscale and analyze
                gray_image = pil_image.convert('L')
                
                # Calculate percentage of white/light pixels as a logo detection method
                pixels = list(gray_image.getdata())
                white_pixels = sum(1 for p in pixels if p > 240)  # Very light pixels
                white_percentage = white_pixels / len(pixels)
                
                # Check if likely a logo based on size and white space
                is_logo = (
                    min_size <= img_size <= max_size and 
                    (white_percentage > logo_detection_threshold or 
                     width/height > 5 or height/width > 5)
                )
                
                if is_logo:
                    # Get image rectangle on the page
                    for img_rect in page.get_image_rects(xref):
                        # Create a white rectangle to cover the logo
                        page.add_redact_annot(img_rect, fill=(1, 1, 1))
                        log_entries.append(f"Logo removed: Page {page.number + 1}, Size: {width}x{height}")
            except Exception as e:
                log_entries.append(f"Logo detection error: Page {page.number + 1}")
                continue
                
        # Apply all redactions at once
        page.apply_redactions()
        
    except Exception as e:
        log_entries.append(f"Logo detection failed on page {page.number + 1}")
        
    return log_entries

def replace_text_in_pdf(pdf_path, words_to_replace, output_path, remove_logos=True):
    """
    Replace sensitive words and optionally remove logos from PDF
    """
    doc = fitz.open(pdf_path)
    log_data = []
    
    for page_num, page in enumerate(doc):
        # First handle logo removal if enabled
        if remove_logos:
            logo_logs = detect_and_remove_logos(page)
            log_data.extend(logo_logs)
        
        # Then handle text replacement
        for word in words_to_replace:
            word_str = str(word).strip()
            if not word_str:
                continue  # Skip empty strings
                
            try:
                # Search for the word on the page
                text_instances = page.search_for(word_str)
                
                if text_instances:
                    log_data.append(f"Text masked: Page {page_num + 1}, Word: '{word_str}'")
                    
                    # Process each instance of the word
                    for inst in text_instances:
                        rect_width = inst[2] - inst[0]  # Get text width
                        num_xxx = max(3, int(rect_width // 6))  # Adjust XXX based on width
                        replacement_text = "X" * num_xxx
                        
                        # Apply white background for proper masking
                        page.add_redact_annot(inst, fill=(1, 1, 1))
                    
                    # Apply all redactions
                    page.apply_redactions()
                    
                    # Add back the XXX text
                    for inst in text_instances:
                        x_start = inst[0]
                        y_start = inst[1] + 5  # Adjusted for alignment
                        page.insert_text((x_start, y_start), replacement_text, fontsize=12, color=(0, 0, 0))
            except Exception as e:
                log_data.append(f"Text masking error: Page {page_num + 1}")
                continue
    
    # Save the processed document
    doc.save(output_path)
    doc.close()
    return log_data

def display_pdf(pdf_path):
    """
    Display PDF in Streamlit using base64 encoding
    """
    try:
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        
        # Use HTML for better preview rendering
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")

def main():
    # Page configuration
    st.set_page_config(
        page_title="Data Shield Platform", 
        page_icon="🔒", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom styling
    st.markdown("""
    <style>
    .title-container {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .title-container h1 {
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .title-container p {
        color: #34495e;
        margin-top: 10px;
    }
    .download-container {
        display: flex;
        justify-content: space-between;
        margin-top: 15px;
    }
    .log-container {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 10px;
        margin-top: 15px;
    }
    .log-entry {
        margin-bottom: 5px;
        padding: 5px;
        background-color: #f1f1f1;
        border-radius: 3px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title and Description
    st.markdown("""
    <div class="title-container">
        <h1>🔒 Data Shield Platform</h1>
        <p>Protect sensitive information by removing confidential text and logos from your documents. 
        Ensure data privacy with our secure PDF masking tool.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Processing Options
    with st.sidebar:
        st.header("🛡️ PDF Processing")
        
        # File Uploaders
        uploaded_pdfs = st.file_uploader(
            "Upload PDFs", 
            type=["pdf"], 
            accept_multiple_files=True,
            help="Select one or more PDFs to process"
        )
        
        uploaded_excel = st.file_uploader(
            "Upload Words to Replace", 
            type=["xlsx"],
            help="Excel file containing words to mask"
        )
        
        # Processing Options
        st.subheader("⚙️ Options")
        remove_logos = st.checkbox(
            "Remove Logos", 
            value=True, 
            help="Detect and remove logo images from documents"
        )
    
    # Sidebar processing button
    with st.sidebar:
        if uploaded_pdfs and uploaded_excel:
            process_button = st.button("🚀 Process PDFs", use_container_width=True)
        else:
            st.info("Upload PDFs and Excel file to enable processing")
    
    # Main processing logic
    if 'process_button' in locals() and process_button:
        try:
            # Read words to replace from Excel
            df = pd.read_excel(BytesIO(uploaded_excel.getvalue()))
            words_to_replace = [str(word).strip() for word in df.iloc[:, 0].dropna().tolist() if str(word).strip()]
            
            # Create downloads directory
            download_dir = "downloads"
            os.makedirs(download_dir, exist_ok=True)
            
            # Save uploaded PDFs
            pdf_paths = []
            for uploaded_pdf in uploaded_pdfs:
                pdf_path = os.path.join(download_dir, uploaded_pdf.name)
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_pdf.getvalue())
                pdf_paths.append(pdf_path)
            
            # Processing spinner
            with st.spinner("Processing PDF(s)..."):
                # Create tabs for multiple PDFs
                tabs = st.tabs([f"PDF {i+1}" for i in range(len(pdf_paths))])
                processed_paths = []
                
                for idx, original_path in enumerate(pdf_paths):
                    with tabs[idx]:
                        # Process individual PDF
                        output_pdf_path = original_path.replace(".pdf", "_masked.pdf")
                        log_data = replace_text_in_pdf(original_path, words_to_replace, output_pdf_path, remove_logos)
                        processed_paths.append(output_pdf_path)
                        
                        # Display original and processed PDFs
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### 📄 Original PDF")
                            display_pdf(original_path)
                        
                        with col2:
                            st.markdown("### 🔒 Processed PDF")
                            display_pdf(output_pdf_path)
                        
                        # Download options
                        col1, col2 = st.columns(2)
                        with col1:
                            with open(original_path, "rb") as f:
                                st.download_button(
                                    "📥 Download Original", 
                                    f, 
                                    file_name=os.path.basename(original_path), 
                                    mime="application/pdf",
                                    key=f"original_download_{idx}"
                                )
                        
                        with col2:
                            with open(output_pdf_path, "rb") as f:
                                st.download_button(
                                    "🔒 Download Masked", 
                                    f, 
                                    file_name=os.path.basename(output_pdf_path), 
                                    mime="application/pdf",
                                    key=f"masked_download_{idx}"
                                )
                        
                        # Professional log display
                        if log_data:
                            st.markdown('<div class="log-container">', unsafe_allow_html=True)
                            st.markdown("### 📋 Processing Details")
                            for entry in log_data:
                                st.markdown(f'<div class="log-entry">{entry}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                
                # Bulk download for multiple PDFs
                if len(processed_paths) > 1:
                    # Create ZIP of processed files
                    zip_path = os.path.join(download_dir, "masked_pdfs.zip")
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for processed_file in processed_paths:
                            zipf.write(processed_file, os.path.basename(processed_file))
                    
                    # Bulk download button
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            "📦 Download All Masked PDFs", 
                            f, 
                            file_name="masked_pdfs.zip", 
                            mime="application/zip"
                        )
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    main()