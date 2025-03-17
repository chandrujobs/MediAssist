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
import zipfile
import numpy as np
from PIL import Image
import io
import tempfile
import concurrent.futures
import time
import shutil
import uuid
import json
import sys

def reload_application():
    """
    This function completely reloads the application.
    It forces a complete page reload, which clears all upload fields.
    Uses a more aggressive approach to ensure file uploaders are reset.
    """
    # Clean up the downloads directory
    if os.path.exists("downloads"):
        try:
            shutil.rmtree("downloads")
            os.makedirs("downloads", exist_ok=True)
        except:
            for file in os.listdir("downloads"):
                try:
                    file_path = os.path.join("downloads", file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except:
                    pass
    
    # Create a reset flag file to signal a complete reset
    with open("reset_flag.txt", "w") as f:
        f.write(f"reset_{uuid.uuid4()}")
    
    # Clear all session state variables
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Generate a unique session ID to force new widget keys
    new_session_id = str(uuid.uuid4())
    
    # Display message
    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;align-items:center;height:100vh;">
            <div style="text-align:center;padding:20px;background-color:#f8f9fa;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <h3>Reloading application...</h3>
                <p>Please wait while the application reloads.</p>
                <p style="font-size:0.8em;color:#6c757d;">Session ID: {new_session_id}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Use JavaScript to force a complete browser reload with cache clearing
    js_code = f"""
    <script>
        // Clear all forms of browser storage
        localStorage.clear();
        sessionStorage.clear();
        
        // Clear any cached form data
        document.cookie.split(";").forEach(function(c) {{
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        }});
        
        // Attempt to clear any file input caches
        try {{
            const fileInputs = document.querySelectorAll('input[type="file"]');
            fileInputs.forEach(input => {{
                input.value = '';
            }});
        }} catch(e) {{}}
        
        // Force a complete page reload from server with unique parameters
        window.location.href = window.location.pathname + 
            "?reload=" + new Date().getTime() + 
            "&sid={new_session_id}";
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)
    st.stop()

def remove_all_logos(page):
    """
    A thorough approach to remove all logos in a document.
    This uses multiple techniques to ensure logos are removed,
    and adds a watermark indicator in place of removed logos.
    """
    log_entries = []
    watermark_areas = []
    
    try:
        # Get page dimensions
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Track logo positions for watermarks
        logo_positions = []
        
        # 1. APPROACH: Target top area of the page (where logos usually appear)
        # Create a rectangle covering the top area of the page
        top_rect = fitz.Rect(0, 0, page_width, page_height * 0.15)
        
        # Store this as a potential watermark location
        watermark_areas.append({
            "rect": top_rect,
            "priority": 3,  # Lower priority
            "type": "header"
        })
        
        page.add_redact_annot(top_rect, fill=(1, 1, 1))
        log_entries.append(f"Applied top area protection on page {page.number + 1}")
        
        # 2. APPROACH: Target all images on the page
        image_rects = []
        try:
            img_list = page.get_images(full=True)
            for img_index, img_info in enumerate(img_list):
                xref = img_info[0]
                
                # Get all instances of this image on the page
                for img_rect in page.get_image_rects(xref):
                    # Expand rectangle slightly to ensure coverage
                    expanded_rect = fitz.Rect(
                        img_rect.x0 - 5, 
                        img_rect.y0 - 5,
                        img_rect.x1 + 5, 
                        img_rect.y1 + 5
                    )
                    
                    # If image is in top section of page, it's likely a logo
                    if expanded_rect.y0 < page_height * 0.2:
                        # Store for watermark with high priority
                        watermark_areas.append({
                            "rect": expanded_rect,
                            "priority": 1,  # High priority
                            "type": "image"
                        })
                    
                    page.add_redact_annot(expanded_rect, fill=(1, 1, 1))
                    image_rects.append(expanded_rect)
                    log_entries.append(f"Removed image on page {page.number + 1}")
        except Exception as e:
            log_entries.append(f"Error processing images: {str(e)}")
        
        # 3. APPROACH: Specifically target common logo positions
        
        # Left side logo
        left_logo_rect = fitz.Rect(
            0,                   # Left
            0,                   # Top
            page_width * 0.40,   # Right
            page_height * 0.12   # Bottom
        )
        page.add_redact_annot(left_logo_rect, fill=(1, 1, 1))
        logo_positions.append(left_logo_rect)
        
        # Add as watermark location
        watermark_areas.append({
            "rect": left_logo_rect,
            "priority": 2,  # Medium priority
            "type": "position"
        })
        
        # Right side logo
        right_logo_rect = fitz.Rect(
            page_width * 0.60,  # Left
            0,                  # Top
            page_width,         # Right
            page_height * 0.12  # Bottom
        )
        page.add_redact_annot(right_logo_rect, fill=(1, 1, 1))
        logo_positions.append(right_logo_rect)
        
        # Add as watermark location
        watermark_areas.append({
            "rect": right_logo_rect,
            "priority": 2,  # Medium priority
            "type": "position"
        })
        
        # Center logo
        center_logo_rect = fitz.Rect(
            page_width * 0.30,  # Left
            0,                  # Top
            page_width * 0.70,  # Right
            page_height * 0.12  # Bottom
        )
        page.add_redact_annot(center_logo_rect, fill=(1, 1, 1))
        logo_positions.append(center_logo_rect)
        
        # Add as watermark location
        watermark_areas.append({
            "rect": center_logo_rect,
            "priority": 2,  # Medium priority
            "type": "position"
        })
        
        log_entries.append(f"Applied targeted protection on page {page.number + 1}")
        
        # 4. APPROACH: Look for all colored elements in header area
        header_area = None
        try:
            header_area = fitz.Rect(0, 0, page_width, page_height * 0.2)
            
            # Get drawings in header area
            drawings = page.get_drawings(rect=header_area)
            
            # If drawings found, redact the entire header
            if drawings and len(drawings) > 0:
                page.add_redact_annot(header_area, fill=(1, 1, 1))
                
                # Add drawing areas as potential watermark locations
                for drawing in drawings:
                    if "rect" in drawing:
                        draw_rect = fitz.Rect(drawing["rect"])
                        if draw_rect.y0 < page_height * 0.2:
                            watermark_areas.append({
                                "rect": draw_rect,
                                "priority": 1,  # High priority
                                "type": "drawing"
                            })
                
                log_entries.append(f"Protected header area with graphics on page {page.number + 1}")
        except Exception as e:
            log_entries.append(f"Error processing header area: {str(e)}")
            
        # 5. APPROACH: Look for specific text patterns that might be part of the logo
        text_logo_rects = []
        try:
            logo_text_patterns = ["Sliced", "Invoices", "SlicedInvoices", "Logo", "Ltd", "Inc", "GmbH", "Software", "Company", "CPB"]
            
            for pattern in logo_text_patterns:
                text_instances = page.search_for(pattern)
                
                for inst in text_instances:
                    # If text is in the top part of the page, likely part of a logo
                    if inst.y1 < page_height * 0.2:
                        # Create a larger rectangle around the text to capture the logo
                        logo_text_rect = fitz.Rect(
                            inst.x0 - 20,
                            inst.y0 - 10,
                            inst.x1 + 150,  # Extend far to the right to capture full logo text
                            inst.y1 + 10
                        )
                        page.add_redact_annot(logo_text_rect, fill=(1, 1, 1))
                        text_logo_rects.append(logo_text_rect)
                        
                        # Add text area as a high priority watermark location
                        watermark_areas.append({
                            "rect": logo_text_rect,
                            "priority": 1,  # High priority
                            "type": "text",
                            "text": pattern
                        })
                        
                        log_entries.append(f"Protected branding text '{pattern}' on page {page.number + 1}")
        except Exception as e:
            log_entries.append(f"Error processing branding text: {str(e)}")
        
        # Apply all redactions at once
        page.apply_redactions()
        
        # Now add watermarks to indicate where logos were removed
        # Sort watermark areas by priority (lower number = higher priority)
        watermark_areas.sort(key=lambda x: x["priority"])
        
        # Keep track of areas where we've already placed watermarks
        watermarked_areas = []
        watermark_added = False
        
        # Process high priority watermark locations first
        for area in watermark_areas:
            rect = area["rect"]
            
            # Skip if this area overlaps with an existing watermark
            should_skip = False
            for placed in watermarked_areas:
                if rect.intersects(placed):
                    intersection = rect.intersect(placed)
                    # If intersection is significant (>30% of either rectangle)
                    if (intersection.get_area() > 0.3 * rect.get_area() or 
                        intersection.get_area() > 0.3 * placed.get_area()):
                        should_skip = True
                        break
            
            if should_skip:
                continue
                
            # Only add watermark if in header area (top 15% of page)
            if rect.y1 < page_height * 0.2:
                # Adjust watermark size to be noticeable but not too large
                # Make sure width is at least 100 points
                adjusted_width = max(100, rect.width * 0.9)
                adjusted_height = max(20, rect.height * 0.9)
                
                border_rect = fitz.Rect(
                    max(0, rect.x0 + (rect.width - adjusted_width) / 2),
                    max(0, rect.y0 + (rect.height - adjusted_height) / 2),
                    min(page_width, rect.x0 + (rect.width + adjusted_width) / 2),
                    min(page_height, rect.y0 + (rect.height + adjusted_height) / 2)
                )
                
                # Ensure minimum size
                if border_rect.width < 40 or border_rect.height < 20:
                    continue
                
                # Draw border with rounded corners and light gray color
                page.draw_rect(border_rect, color=(0.7, 0.0, 0.7), width=1, dashes="[1 1]", 
                              fill=(0.98, 0.9, 0.98), fill_opacity=0.3)
                
                # Add "LOGO" text in center of rectangle with larger font
                text_point = fitz.Point(
                    (border_rect.x0 + border_rect.x1) / 2,
                    (border_rect.y0 + border_rect.y1) / 2
                )
                page.insert_text(text_point, "LOGO", 
                               color=(0.7, 0.0, 0.7), fontsize=14,
                               fontname="Helvetica-Bold",
                               align=1)  # 1 = center aligned
                
                watermarked_areas.append(border_rect)
                watermark_added = True
                log_entries.append(f"Added logo watermark indicator on page {page.number + 1}")
                
                # If we've added 3 watermarks, stop to avoid cluttering the page
                if len(watermarked_areas) >= 3:
                    break
        
        # If no specific watermarks were added, add a general one to the header area
        if not watermark_added and header_area:
            # Add a general watermark to the header area
            header_watermark_rect = fitz.Rect(
                page_width * 0.4,    # Left
                page_height * 0.02,  # Top
                page_width * 0.6,    # Right
                page_height * 0.08   # Bottom
            )
            
            # Draw border with rounded corners and light gray color
            page.draw_rect(header_watermark_rect, color=(0.7, 0.0, 0.7), width=1, dashes="[1 1]", 
                          fill=(0.98, 0.9, 0.98), fill_opacity=0.3)
            
            # Add "LOGO" text in center of rectangle
            text_point = fitz.Point(
                (header_watermark_rect.x0 + header_watermark_rect.x1) / 2,
                (header_watermark_rect.y0 + header_watermark_rect.y1) / 2
            )
            page.insert_text(text_point, "LOGO", 
                           color=(0.7, 0.0, 0.7), fontsize=14,
                           fontname="Helvetica-Bold",
                           align=1)  # 1 = center aligned
            
            log_entries.append(f"Added general header watermark indicator on page {page.number + 1}")
        
    except Exception as e:
        log_entries.append(f"Error in brand protection: {str(e)}")
        
    return log_entries

def replace_text_efficiently(page, words_to_replace):
    """
    Efficient version of text replacement that minimizes redaction operations.
    """
    log_entries = []
    text_instances = []
    
    # First collect all instances of words to replace
    for word in words_to_replace:
        word_str = str(word).strip()
        if not word_str:
            continue
            
        try:
            # Search for all instances of this word
            instances = page.search_for(word_str)
            if instances:
                text_instances.extend(instances)
                log_entries.append(f"Found word to mask: '{word_str}' on page {page.number + 1}")
        except Exception:
            continue
    
    # If we found words to replace
    if text_instances:
        # Add redactions for all instances at once
        for inst in text_instances:
            page.add_redact_annot(inst, fill=(1, 1, 1))
        
        # Apply all redactions in one operation
        page.apply_redactions()
        
        # Add replacement text
        for inst in text_instances:
            rect_width = inst[2] - inst[0]
            num_xxx = max(3, int(rect_width // 6))
            replacement_text = "X" * num_xxx
            
            x_start = inst[0]
            y_start = inst[1] + 5
            page.insert_text((x_start, y_start), replacement_text, fontsize=12, color=(0, 0, 0))
    
    return log_entries

def process_pdf_with_enhanced_protection(pdf_path, words_to_replace, output_path, remove_logos=True, add_watermarks=True):
    """
    Process a PDF with enhanced logo protection.
    Uses a thorough approach to ensure all logos are removed.
    Optionally adds watermarks to indicate where logos were removed.
    """
    doc = fitz.open(pdf_path)
    log_data = []
    
    # First handle logo removal if enabled
    if remove_logos:
        for page_num in range(len(doc)):
            page = doc[page_num]
            logo_logs = remove_all_logos(page) if add_watermarks else remove_logos_without_watermark(page)
            log_data.extend(logo_logs)
    
    # Then handle text replacement
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_logs = replace_text_efficiently(page, words_to_replace)
        log_data.extend(text_logs)
    
    # Save the processed document
    doc.save(output_path)
    doc.close()
    return log_data

def remove_logos_without_watermark(page):
    """
    Original logo removal function without watermarks.
    Kept for backward compatibility.
    """
    log_entries = []
    
    try:
        # Get page dimensions
        page_width = page.rect.width
        page_height = page.rect.height
        
        # 1. APPROACH: Target top area of the page (where logos usually appear)
        # Create a rectangle covering the top area of the page
        top_rect = fitz.Rect(0, 0, page_width, page_height * 0.15)
        page.add_redact_annot(top_rect, fill=(1, 1, 1))
        log_entries.append(f"Applied top area protection on page {page.number + 1}")
        
        # 2. APPROACH: Target all images on the page
        try:
            img_list = page.get_images(full=True)
            for img_index, img_info in enumerate(img_list):
                xref = img_info[0]
                
                # Get all instances of this image on the page
                for img_rect in page.get_image_rects(xref):
                    # Expand rectangle slightly to ensure coverage
                    expanded_rect = fitz.Rect(
                        img_rect.x0 - 5, 
                        img_rect.y0 - 5,
                        img_rect.x1 + 5, 
                        img_rect.y1 + 5
                    )
                    page.add_redact_annot(expanded_rect, fill=(1, 1, 1))
                    log_entries.append(f"Removed image on page {page.number + 1}")
        except Exception as e:
            log_entries.append(f"Error processing images: {str(e)}")
        
        # 3. APPROACH: Specifically target common logo positions
        # Left side logo
        left_logo_rect = fitz.Rect(
            0,                   # Left
            0,                   # Top
            page_width * 0.40,   # Right
            page_height * 0.12   # Bottom
        )
        page.add_redact_annot(left_logo_rect, fill=(1, 1, 1))
        
        # Right side logo
        right_logo_rect = fitz.Rect(
            page_width * 0.60,  # Left
            0,                  # Top
            page_width,         # Right
            page_height * 0.12  # Bottom
        )
        page.add_redact_annot(right_logo_rect, fill=(1, 1, 1))
        
        # Center logo
        center_logo_rect = fitz.Rect(
            page_width * 0.30,  # Left
            0,                  # Top
            page_width * 0.70,  # Right
            page_height * 0.12  # Bottom
        )
        page.add_redact_annot(center_logo_rect, fill=(1, 1, 1))
        
        log_entries.append(f"Applied targeted protection on page {page.number + 1}")
        
        # 4. APPROACH: Look for all colored elements in header area
        # This is particularly effective for logos with distinctive colors
        try:
            header_area = fitz.Rect(0, 0, page_width, page_height * 0.2)
            
            # Get drawings in header area
            drawings = page.get_drawings(rect=header_area)
            
            # If drawings found, redact the entire header
            if drawings and len(drawings) > 0:
                page.add_redact_annot(header_area, fill=(1, 1, 1))
                log_entries.append(f"Protected header area with graphics on page {page.number + 1}")
        except Exception as e:
            log_entries.append(f"Error processing header area: {str(e)}")
            
        # 5. APPROACH: Look for specific text patterns that might be part of the logo
        try:
            logo_text_patterns = ["Sliced", "Invoices", "SlicedInvoices", "Logo", "Ltd", "Inc", "GmbH", "Software", "Company"]
            
            for pattern in logo_text_patterns:
                text_instances = page.search_for(pattern)
                
                for inst in text_instances:
                    # If text is in the top part of the page, likely part of a logo
                    if inst.y1 < page_height * 0.2:
                        # Create a larger rectangle around the text to capture the logo
                        logo_text_rect = fitz.Rect(
                            inst.x0 - 20,
                            inst.y0 - 10,
                            inst.x1 + 150,  # Extend far to the right to capture full logo text
                            inst.y1 + 10
                        )
                        page.add_redact_annot(logo_text_rect, fill=(1, 1, 1))
                        log_entries.append(f"Protected branding text '{pattern}' on page {page.number + 1}")
        except Exception as e:
            log_entries.append(f"Error processing branding text: {str(e)}")
        
        # Apply all redactions at once
        page.apply_redactions()
        
    except Exception as e:
        log_entries.append(f"Error in brand protection: {str(e)}")
        
    return log_entries

def generate_preview(pdf_path, max_pages=3):
    """
    Generate a preview of a PDF efficiently by processing only the first few pages.
    For large documents, we want to avoid loading the entire document for preview.
    """
    try:
        # Open the document
        doc = fitz.open(pdf_path)
        
        # Determine number of pages to preview
        num_pages = min(max_pages, len(doc))
        
        # Create a new document for preview
        preview_doc = fitz.open()
        
        # Add first few pages to preview
        for i in range(num_pages):
            preview_doc.insert_pdf(doc, from_page=i, to_page=i)
        
        # Create bytes for preview
        preview_bytes = preview_doc.tobytes()
        
        # Clean up
        preview_doc.close()
        doc.close()
        
        return preview_bytes
    
    except Exception as e:
        print(f"Error generating preview: {e}")
        return None

def display_pdf_preview(pdf_bytes):
    """
    Display a PDF preview from bytes without having to save the file.
    """
    try:
        # Encode PDF bytes to base64
        if pdf_bytes:
            base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            
            # Use HTML for efficient preview rendering
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.error("No PDF data available for preview")
    except Exception as e:
        st.error(f"Error displaying PDF preview: {str(e)}")

def display_pdf_file(pdf_path, max_preview_size_mb=10):
    """
    Display a PDF file with size limit for preview.
    For very large files, show only a preview of the first few pages.
    """
    try:
        # Check file size
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        
        if file_size_mb > max_preview_size_mb:
            st.warning(f"Large PDF ({file_size_mb:.1f} MB). Showing preview of first few pages only.")
            # Generate and display preview
            preview_bytes = generate_preview(pdf_path)
            display_pdf_preview(preview_bytes)
        else:
            # For smaller files, display the whole thing
            with open(pdf_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            
            # Use HTML for better preview rendering
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")

def check_for_reset_flag():
    """
    Check if a reset flag file exists and handle the reset process.
    """
    if os.path.exists("reset_flag.txt"):
        try:
            # Read the flag to get unique session ID
            with open("reset_flag.txt", "r") as f:
                reset_id = f.read().strip()
            
            # Remove the flag file
            os.remove("reset_flag.txt")
            
            # Set a completely new run ID
            st.session_state.run_id = str(uuid.uuid4())
            
            # Force reload one more time to complete the reset
            js_code = f"""
            <script>
                // Force another reload without the flag file
                window.location.href = window.location.pathname + 
                    "?complete_reset=true&ts={time.time()}&rid={reset_id}";
            </script>
            """
            st.markdown(js_code, unsafe_allow_html=True)
            st.stop()
            
        except Exception as e:
            print(f"Error handling reset flag: {e}")
            if os.path.exists("reset_flag.txt"):
                try:
                    os.remove("reset_flag.txt")
                except:
                    pass

def main():
    # Check for reset flag first
    check_for_reset_flag()
    
    # Set a unique run ID if not already present
    if "run_id" not in st.session_state:
        st.session_state.run_id = str(uuid.uuid4())
    
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
        max-height: 200px;
        overflow-y: auto;
    }
    .log-entry {
        margin-bottom: 5px;
        padding: 3px;
        font-size: 0.9em;
        background-color: #f1f1f1;
        border-radius: 3px;
    }
    .stButton button {
        font-weight: 500;
    }
    .reset-button button {
        background-color: #3498db;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title and Description
    st.markdown("""
    <div class="title-container">
        <h1>🔒 Data Shield Platform</h1>
        <p>Protect sensitive information by removing confidential text and logos from your documents.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for tracking processed files
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []
    
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
        
        if 'enhanced_protection' not in st.session_state:
            st.session_state.enhanced_protection = True
            
        enhanced_protection = st.checkbox(
            "Enhanced Logo Protection", 
            value=st.session_state.enhanced_protection,
            key=f"enhanced_protection_{run_id}",
            help="Ensures complete removal of all logo elements (recommended)"
        )
        # Update session state when the checkbox is changed
        st.session_state.enhanced_protection = enhanced_protection
        
        if 'add_watermarks' not in st.session_state:
            st.session_state.add_watermarks = True
            
        add_watermarks = st.checkbox(
            "Add 'Logo Present' Indicators", 
            value=st.session_state.add_watermarks,
            key=f"add_watermarks_{run_id}",
            help="Add light gray indicators showing where logos were originally present"
        )
        # Update session state when the checkbox is changed
        st.session_state.add_watermarks = add_watermarks
    
    # Function to clear uploads - more aggressive approach
    def clear_uploads():
        """
        Clear all uploaded files and force component reset
        """
        # Generate a new unique ID to force widget recreation
        new_run_id = str(uuid.uuid4())
        st.session_state.run_id = new_run_id
        
        # Clear all file upload related keys from session state
        for key in list(st.session_state.keys()):
            if 'uploader' in key or 'uploaded' in key:
                del st.session_state[key]
        
        # Force component to recreate with rerun
        st.rerun()

    
    # Sidebar processing button and reset button
    with st.sidebar:
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
        
        # Reset button (formerly Clear Uploads)
        st.markdown('<div class="reset-button">', unsafe_allow_html=True)
        if st.button("🔄 Reset", key=f"reset_button_{run_id}", use_container_width=True):
            clear_uploads()
        st.markdown('</div>', unsafe_allow_html=True)
    
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
                        status_text.text("Generating preview...")
                        display_pdf_file(original_path)
                    
                    # Define output path
                    output_pdf_path = original_path.replace(".pdf", "_masked.pdf")
                    
                    # Process document with progress updates
                    status_text.text("Processing document...")
                    progress_bar.progress(25)
                    
                    # Process PDF with enhanced protection
                    start_time = time.time()
                    log_data = process_pdf_with_enhanced_protection(
                        original_path, 
                        words_to_replace, 
                        output_pdf_path, 
                        remove_logos,
                        st.session_state.add_watermarks
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
                    col1, col2 = st.columns(2)
                    with col1:
                        with open(output_pdf_path, "rb") as f:
                            st.download_button(
                                "🔒 Download Processed PDF", 
                                f, 
                                file_name=f"masked_{os.path.basename(original_path)}",
                                mime="application/pdf",
                                use_container_width=True
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
                
                # Bulk download button
                with open(zip_path, "rb") as f:
                    st.download_button(
                        "📦 Download All Processed PDFs as ZIP", 
                        f, 
                        file_name="masked_pdfs.zip", 
                        mime="application/zip",
                        use_container_width=True
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
