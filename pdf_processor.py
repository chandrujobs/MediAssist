# Save this as pdf_processor.py in your test directory
import fitz  # PyMuPDF
import os
import base64
import io
import tempfile

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
            return pdf_display
        else:
            return "<p>No PDF data available for preview</p>"
    except Exception as e:
        return f"<p>Error displaying PDF preview: {str(e)}</p>"

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

def display_pdf_file(pdf_path, max_preview_size_mb=10):
    """
    Display a PDF file with size limit for preview.
    For very large files, show only a preview of the first few pages.
    """
    import streamlit as st
    
    try:
        # Check file size
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        
        if file_size_mb > max_preview_size_mb:
            st.warning(f"Large PDF ({file_size_mb:.1f} MB). Showing preview of first few pages only.")
            # Generate and display preview
            preview_bytes = generate_preview(pdf_path)
            preview_html = display_pdf_preview(preview_bytes)
            st.markdown(preview_html, unsafe_allow_html=True)
        else:
            # For smaller files, display the whole thing
            with open(pdf_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            
            # Use HTML for better preview rendering
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")

def analyze_pdf_quality(pdf_path):
    """
    Analyzes PDF quality based on three metrics:
    1. Text extraction quality
    2. Image resolution quality
    3. Document structure quality
    
    Returns a dict with quality scores (0-5) and an overall score.
    """
    try:
        doc = fitz.open(pdf_path)
        quality_metrics = {
            "text_quality": 0,
            "image_quality": 0, 
            "structure_quality": 0,
            "overall_score": 0,
            "details": []
        }
        
        # 1. Text extraction quality
        total_text_length = 0
        total_pages = len(doc)
        searchable_pages = 0
        
        for page_num in range(min(10, total_pages)):  # Check up to 10 pages
            page = doc[page_num]
            text = page.get_text()
            if len(text.strip()) > 50:  # Page has meaningful text
                searchable_pages += 1
            total_text_length += len(text)
        
        # Calculate text quality score
        if total_pages > 0:
            text_searchable_ratio = searchable_pages / min(10, total_pages)
            if text_searchable_ratio > 0.9:
                text_score = 5  # Excellent
            elif text_searchable_ratio > 0.7:
                text_score = 4  # Good
            elif text_searchable_ratio > 0.5:
                text_score = 3  # Average
            elif text_searchable_ratio > 0.3:
                text_score = 2  # Below average
            elif text_searchable_ratio > 0.1:
                text_score = 1  # Poor
            else:
                text_score = 0  # Very poor
                
            quality_metrics["text_quality"] = text_score
            if text_score <= 2:
                quality_metrics["details"].append("Low text extraction quality. PDF may be scanned or have text as images.")
            
        # 2. Image resolution quality
        total_images = 0
        high_res_images = 0
        
        for page_num in range(min(5, total_pages)):  # Check up to 5 pages
            page = doc[page_num]
            img_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(img_list):
                total_images += 1
                xref = img_info[0]
                
                try:
                    base_image = doc.extract_image(xref)
                    if base_image:
                        pix_width = base_image.get("width", 0)
                        pix_height = base_image.get("height", 0)
                        
                        # Check for high resolution (assume images should be at least 150 DPI)
                        if pix_width > 1000 or pix_height > 1000:
                            high_res_images += 1
                except Exception:
                    pass
        
        # Calculate image quality score
        if total_images > 0:
            image_quality_ratio = high_res_images / total_images
            if image_quality_ratio > 0.9:
                image_score = 5  # Excellent
            elif image_quality_ratio > 0.7:
                image_score = 4  # Good
            elif image_quality_ratio > 0.5:
                image_score = 3  # Average
            elif image_quality_ratio > 0.3:
                image_score = 2  # Below average
            elif image_quality_ratio > 0.1:
                image_score = 1  # Poor
            else:
                image_score = 0  # Very poor
                
            quality_metrics["image_quality"] = image_score
            if image_score <= 2 and total_images > 0:
                quality_metrics["details"].append("Low image resolution quality. Images may appear blurry when printed.")
        elif total_images == 0:
            # No images, so not applicable - give middle score
            quality_metrics["image_quality"] = 3
            
        # 3. Document structure quality
        has_bookmarks = len(doc.get_toc()) > 0
        has_metadata = bool(doc.metadata)
        
        # Check for document structure elements
        structure_score = 0
        if has_bookmarks:
            structure_score += 2  # Good structure with bookmarks/TOC
        if has_metadata:
            structure_score += 1  # Has proper metadata
            
        # Check page layout consistency
        page_sizes = set()
        for page_num in range(min(10, total_pages)):
            page = doc[page_num]
            page_sizes.add((page.rect.width, page.rect.height))
        
        if len(page_sizes) == 1:
            structure_score += 2  # Consistent page sizes
        else:
            structure_score = max(0, structure_score - 1)  # Penalize for inconsistent sizes
            
        quality_metrics["structure_quality"] = min(5, structure_score)
        if structure_score <= 2:
            quality_metrics["details"].append("Low document structure quality. PDF may lack bookmarks, metadata, or have inconsistent page sizes.")
        
        # Calculate overall score (weighted average)
        quality_metrics["overall_score"] = round((quality_metrics["text_quality"] * 0.5) + 
                                                (quality_metrics["image_quality"] * 0.3) + 
                                                (quality_metrics["structure_quality"] * 0.2))
        
        doc.close()
        return quality_metrics
        
    except Exception as e:
        # If analysis fails, return default low scores
        return {
            "text_quality": 1,
            "image_quality": 1,
            "structure_quality": 1,
            "overall_score": 1,
            "details": [f"Error analyzing PDF quality: {str(e)}"]
        }

def remove_all_logos(page, add_watermarks=True):
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
            # Expanded list of common logo text patterns
            logo_text_patterns = [
                "Sliced", "Invoices", "SlicedInvoices", "Logo", "Ltd", "Inc", 
                "GmbH", "Software", "Company", "CPB", "Limited", "Corp", 
                "Corporation", "Technologies", "Tech", "Solutions", "Systems",
                "Services", "Group", "International", "Holdings", "Enterprises"
            ]
            
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
        
        # Now add watermarks to indicate where logos were removed (if enabled)
        if add_watermarks:
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
                    
                    # Draw border with rounded corners and light purple color
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
                
                # Draw border with rounded corners and light purple color
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
        
        # Apply all redactions at once
        page.apply_redactions()
        
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
            logo_logs = remove_all_logos(page, add_watermarks)
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
