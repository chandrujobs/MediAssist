import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import io
import tempfile
import concurrent.futures

def detect_scanned_pdf(pdf_path):
    """
    Detect if a PDF is a scanned document.
    """
    doc = fitz.open(pdf_path)
    is_scanned = False
    
    try:
        # Check a sample of pages (maximum 3 pages)
        max_pages = min(3, len(doc))
        
        for page_num in range(max_pages):
            page = doc[page_num]
            
            # Get text information
            text = page.get_text()
            words = page.get_text("words")
            
            # Check if the page has almost no text but has images
            has_images = len(page.get_images()) > 0
            
            # If the page has very few words but has images, it's likely scanned
            if (len(words) < 10 and has_images) or (len(text.strip()) < 50 and has_images):
                is_scanned = True
                break
                
            # Check if text characters are scattered unusually (OCR artifact)
            if len(words) > 0:
                # Calculate average word length
                avg_word_length = sum(len(word[4]) for word in words) / len(words)
                
                # If average word length is very short, might be OCR artifacts
                if avg_word_length < 2.5:
                    is_scanned = True
                    break
                    
                # Check for unusual character spacing (common in OCR)
                unusual_spacing = 0
                for word in words:
                    if len(word[4]) > 2:
                        word_str = word[4]
                        for i in range(len(word_str) - 1):
                            # Check for unusual spacing between characters
                            if word[2] - word[0] > 0 and len(word_str) > 1:
                                char_width = (word[2] - word[0]) / len(word_str)
                                if char_width > 20:  # Unusually wide spacing
                                    unusual_spacing += 1
                
                # If more than 30% of words have unusual spacing, likely a scanned PDF
                if unusual_spacing > 0 and unusual_spacing > len(words) * 0.3:
                    is_scanned = True
                    break
                    
    except Exception as e:
        print(f"Error detecting scanned PDF: {str(e)}")
        # If we encounter an error, treat it as non-scanned to use standard processing
        is_scanned = False
        
    doc.close()
    return is_scanned
    
def extract_small_text(page, min_font_size=6):
    """
    Extract text instances that have small font sizes, which might be missed in normal search.
    """
    text_instances = []
    
    try:
        # Get all text spans on the page
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    if "spans" in line:
                        for span in line["spans"]:
                            # Check if font size is small
                            if span.get("size", 0) <= min_font_size:
                                text = span.get("text", "").strip()
                                if text:
                                    # Create a rectangle for this text
                                    bbox = fitz.Rect(span["bbox"])
                                    text_instances.append((text, bbox))
    except Exception as e:
        print(f"Error extracting small text: {str(e)}")
        
    return text_instances

def enhance_image_for_text_detection(page, dpi=300):
    """
    Extract images from the page and enhance them for better text detection.
    This is particularly useful for scanned documents where text is embedded in images.
    """
    enhanced_images = []
    
    try:
        # Extract images
        image_list = page.get_images(full=True)
        
        for img_idx, img in enumerate(image_list):
            xref = img[0]
            base_image = page.parent.extract_image(xref)
            
            if base_image:
                # Get image data
                image_bytes = base_image["image"]
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # Convert to grayscale for better text contrast
                gray_image = image.convert('L')
                
                # Enhance contrast
                enhanced = np.array(gray_image)
                enhanced = np.clip((enhanced.astype(np.int16) * 1.5), 0, 255).astype(np.uint8)
                
                # Convert back to PIL Image
                enhanced_image = Image.fromarray(enhanced)
                
                # Get image placement on page
                for img_rect in page.get_image_rects(xref):
                    enhanced_images.append((enhanced_image, img_rect))
    except Exception as e:
        print(f"Error enhancing images: {str(e)}")
        
    return enhanced_images

def process_text_in_words(page, words_to_replace):
    """
    Process text in a scanned document, using a more thorough approach.
    This handles small text and text that might be missed in regular search.
    """
    log_entries = []
    
    # First try standard search for words
    for word in words_to_replace:
        word_str = str(word).strip()
        if not word_str:
            continue
            
        try:
            # Search for all instances of this word
            instances = page.search_for(word_str)
            
            if instances:
                for inst in instances:
                    # Add a redaction annotation
                    page.add_redact_annot(inst, fill=(1, 1, 1))
                    log_entries.append(f"Found standard word to mask: '{word_str}' on page {page.number + 1}")
                    
        except Exception as e:
            log_entries.append(f"Error searching for word '{word_str}': {str(e)}")
    
    # Apply all redactions at once
    redaction_count = page.apply_redactions()
    if redaction_count > 0:
        log_entries.append(f"Applied {redaction_count} redactions on page {page.number + 1}")
    
    # Get small text that might be missed in regular search
    small_text_instances = extract_small_text(page)
    
    small_text_redactions = 0
    for text, bbox in small_text_instances:
        for word in words_to_replace:
            word_str = str(word).strip().lower()
            if word_str and word_str in text.lower():
                # Add a redaction annotation
                page.add_redact_annot(bbox, fill=(1, 1, 1))
                log_entries.append(f"Found small text to mask: '{text}' on page {page.number + 1}")
                small_text_redactions += 1
                break
    
    # Apply small text redactions
    if small_text_redactions > 0:
        page.apply_redactions()
        log_entries.append(f"Applied {small_text_redactions} small text redactions on page {page.number + 1}")
    
    return log_entries

def process_scanned_pdf(pdf_path, words_to_replace, output_path, remove_logos=True, add_watermarks=True):
    """
    Process a scanned PDF, with specific optimizations for handling text in images
    and small text that might be missed in normal processing.
    """
    doc = fitz.open(pdf_path)
    log_data = []
    
    # Handle logo removal first, similar to regular PDFs
    if remove_logos:
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Use enhanced protection always enabled for scanned PDFs
            from pdf_processor import remove_all_logos
            logo_logs = remove_all_logos(page, add_watermarks)
            log_data.extend(logo_logs)
    
    # Enhanced text replacement for scanned documents
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_page = {}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            future = executor.submit(process_text_in_words, page, words_to_replace)
            future_to_page[future] = page_num
        
        for future in concurrent.futures.as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                log_entries = future.result()
                log_data.extend(log_entries)
            except Exception as e:
                log_data.append(f"Error processing page {page_num}: {str(e)}")
    
    # Save the processed document
    doc.save(output_path)
    doc.close()
    
    return log_data
