import streamlit as st
import pandas as pd
import os
from io import BytesIO
import base64
import zipfile
import time
import uuid
import sys

from pdf_processor import process_pdf_with_enhanced_protection, display_pdf_file, generate_preview, display_pdf_preview
from scanned_files import detect_scanned_pdf, process_scanned_pdf
from reset import check_for_reset_flag, clear_uploads

def main():
    # Check for reset flag first
    check_for_reset_flag()
    
    # Set a unique run ID if not already present
    if "run_id" not in st.session_state:
        st.session_state.run_id = str(uuid.uuid4())
    
    # Initialize session state for tracking processed files
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []
    
    # Page configuration
    st.set_page_config(
        page_title="Data Shield Platform", 
        page_icon="🔒", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Title and Description
    st.markdown("""
    <div class="title-container">
        <h1>🔒 Data Shield Platform</h1>
        <p>Protect sensitive information by removing confidential text and logos from your documents.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content and sidebar setup
    main_content = st.container()
    
    # Sidebar Processing Options
    with st.sidebar:
        st.header("🛡️ PDF Processing")
        
        # Use the run_id to ensure unique widget IDs
        run_id = st.session_state.run_id
        
        # File Uploaders - use keys based on current run_id
        uploaded_pdfs = st.file_uploader(
            "Upload PDFs", 
            type=["pdf"], 
            accept_multiple_files=True,
            key=f"pdf_uploader_{run_id}",
            help="Select one or more PDFs to process"
        )
        
        uploaded_excel = st.file_uploader(
            "Upload Words to Replace", 
            type=["xlsx"],
            key=f"excel_uploader_{run_id}",
            help="Excel file containing words to mask"
        )
        
        # Store the uploaders in session state to ensure they're cleared on reload
        if uploaded_pdfs is not None:
            st.session_state.uploaded_pdfs = uploaded_pdfs
        if uploaded_excel is not None:
            st.session_state.uploaded_excel = uploaded_excel
            
            # Display the words to be masked from the Excel file
            try:
                df = pd.read_excel(BytesIO(uploaded_excel.getvalue()))
                words_to_replace = [str(word).strip() for word in df.iloc[:, 0].dropna().tolist() if str(word).strip()]
                
                if words_to_replace:
                    with st.expander("Words to be masked", expanded=False):
                        st.write("The following words will be masked in your documents:")
                        for i, word in enumerate(words_to_replace[:20]):  # Limit to first 20 words
                            st.write(f"• {word}")
                        if len(words_to_replace) > 20:
                            st.write(f"• ... and {len(words_to_replace) - 20} more")
            except Exception as e:
                st.error(f"Error reading Excel file: {str(e)}")
        
        # Processing Options
        st.subheader("⚙️ Options")
        
        # Use the run_id to ensure unique checkbox IDs
        if 'remove_logos' not in st.session_state:
            st.session_state.remove_logos = True
        
        remove_logos = st.checkbox(
            "Remove Logos", 
            value=st.session_state.remove_logos,
            key=f"remove_logos_{run_id}",
            help="Detect and remove logo images from documents"
        )
        # Update session state when the checkbox is changed
        st.session_state.remove_logos = remove_logos
        
        if 'add_watermarks' not in st.session_state:
            st.session_state.add_watermarks = True
            
        add_watermarks = st.checkbox(
            "Add Logo Placeholders", 
            value=st.session_state.add_watermarks,
            key=f"add_watermarks_{run_id}",
            help="Add light purple indicators showing where logos were originally present"
        )
        # Update session state when the checkbox is changed
        st.session_state.add_watermarks = add_watermarks
        
        # Hidden option - always set to true but not shown in sidebar
        if 'handle_scanned_pdfs' not in st.session_state:
            st.session_state.handle_scanned_pdfs = True
        
        # Process button
        if uploaded_pdfs and uploaded_excel:
            process_button = st.button(
                "🚀 Process PDFs", 
                key=f"process_button_{run_id}", 
                use_container_width=True
            )
        else:
            st.info("Upload PDFs and Excel file to enable processing")
        
        # Add some space
        st.markdown("###")
        
        # Reset button
        st.markdown('<div class="reset-button">', unsafe_allow_html=True)
        if st.button("🔄 Reset", key=f"reset_button_{run_id}", use_container_width=True):
            clear_uploads()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main processing logic
    with main_content:
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
                
                # Create tabs for multiple PDFs
                tabs = st.tabs([f"PDF {i+1}: {os.path.basename(path)}" for i, path in enumerate(pdf_paths)])
                processed_paths = []
                
                # Process each PDF
                for idx, original_path in enumerate(pdf_paths):
                    with tabs[idx]:
                        # Create progress indicator
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Show original document preview
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### 📄 Original PDF")
                            
                            # Generate preview and show document
                            status_text.text("Generating preview...")
                            file_size_mb = os.path.getsize(original_path) / (1024 * 1024)
                            if file_size_mb > 10:
                                st.warning(f"Large PDF ({file_size_mb:.1f} MB). Showing preview of first few pages only.")
                                # For large files, only show first 5 pages for faster loading
                                preview_bytes = generate_preview(original_path, max_pages=5)
                                pdf_html = display_pdf_preview(preview_bytes)
                                st.markdown(pdf_html, unsafe_allow_html=True)
                            else:
                                display_pdf_file(original_path)
                        
                        # Define output path
                        output_pdf_path = original_path.replace(".pdf", "_masked.pdf")
                        
                        # Process document with progress updates
                        status_text.text("Checking document type...")
                        progress_bar.progress(10)
                        
                        # Check if this is a scanned PDF - always enabled but hidden from UI
                        is_scanned = detect_scanned_pdf(original_path)
                        if is_scanned:
                            status_text.text("Detected scanned PDF. Using optimized processing...")
                            progress_bar.progress(25)
                            
                            # Process scanned PDF with special handling
                            start_time = time.time()
                            log_data = process_scanned_pdf(
                                original_path, 
                                words_to_replace, 
                                output_pdf_path,
                                remove_logos=st.session_state.remove_logos,
                                add_watermarks=st.session_state.add_watermarks
                            )
                            processing_time = time.time() - start_time
                        else:
                            status_text.text("Processing document...")
                            progress_bar.progress(25)
                            
                            # Process PDF with enhanced protection
                            start_time = time.time()
                            log_data = process_pdf_with_enhanced_protection(
                                original_path, 
                                words_to_replace, 
                                output_pdf_path, 
                                remove_logos=st.session_state.remove_logos,
                                add_watermarks=st.session_state.add_watermarks
                            )
                            processing_time = time.time() - start_time
                        
                        progress_bar.progress(75)
                        processed_paths.append(output_pdf_path)
                        
                        # Track processed files in session state
                        st.session_state.processed_files.append(output_pdf_path)
                        
                        # Show processed document preview
                        with col2:
                            st.markdown("### 🔒 Processed PDF")
                            status_text.text("Generating processed preview...")
                            display_pdf_file(output_pdf_path)
                        
                        # Update progress and status
                        progress_bar.progress(100)
                        status_text.text(f"Processing complete in {processing_time:.2f} seconds")
                        
                        # Download buttons
                        st.markdown("### 📥 Download Options")
                        col_download1, col_download2 = st.columns(2)
                        
                        # Store download state to maintain previews after download
                        if f"downloaded_{idx}" not in st.session_state:
                            st.session_state[f"downloaded_{idx}"] = False
                            
                        def set_downloaded(idx):
                            st.session_state[f"downloaded_{idx}"] = True
                            
                        with col_download1:
                            with open(output_pdf_path, "rb") as f:
                                st.download_button(
                                    "🔒 Download Processed PDF", 
                                    f, 
                                    file_name=f"masked_{os.path.basename(original_path)}",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    on_click=set_downloaded,
                                    args=(idx,)
                                )
                        
                        # Professional log display (with limit to avoid overloading UI)
                        if log_data:
                            st.markdown("### 📋 Processing Log")
                            with st.expander("View Processing Details"):
                                st.markdown('<div class="log-container">', unsafe_allow_html=True)
                                # Show only the most important logs (limit to 50)
                                displayed_logs = log_data if len(log_data) < 50 else log_data[:50]
                                for entry in displayed_logs:
                                    st.markdown(f'<div class="log-entry">{entry}</div>', unsafe_allow_html=True)
                                if len(log_data) > 50:
                                    st.markdown(f'<div class="log-entry">...and {len(log_data) - 50} more entries</div>', unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                
                # Bulk download for multiple PDFs
                if len(processed_paths) > 1:
                    st.markdown("### 📦 Batch Download")
                    # Create ZIP of processed files
                    zip_path = os.path.join(download_dir, "masked_pdfs.zip")
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for processed_file in processed_paths:
                            zipf.write(processed_file, os.path.basename(processed_file))
                    
                    # Define a callback for batch download
                    def batch_download_callback():
                        for i in range(len(processed_paths)):
                            st.session_state[f"downloaded_{i}"] = True
                    
                    # Bulk download button
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            "📦 Download All Processed PDFs as ZIP", 
                            f, 
                            file_name="masked_pdfs.zip", 
                            mime="application/zip",
                            use_container_width=True,
                            on_click=batch_download_callback
                        )
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Ensure downloads directory exists
    os.makedirs("downloads", exist_ok=True)
    
    # Add query parameters to URL to help with cache busting
    query_params = st.query_params
    if "reload" in query_params:
        # This is a reload request, make sure we have a fresh session
        for key in list(st.session_state.keys()):
            # Keep only essential state if needed
            if key not in ["run_id"]:
                del st.session_state[key]
    
    # Run the application
    main()
