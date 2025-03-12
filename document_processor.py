import os
from pypdf import PdfReader

def process_documents(documents_folder):
    """
    Process all PDF documents in a folder and return chunks.
    
    Args:
        documents_folder (str): Folder containing PDF documents
        
    Returns:
        list: List of text chunks from all documents
    """
    all_chunks = []
    
    if not os.path.exists(documents_folder):
        print(f"Documents folder {documents_folder} does not exist.")
        return all_chunks
    
    for filename in os.listdir(documents_folder):
        if filename.endswith('.pdf'):
            file_path = os.path.join(documents_folder, filename)
            print(f"Processing {filename}...")
            
            try:
                # Extract text from PDF - limit to 10 pages for speed
                pdf_reader = PdfReader(file_path)
                text = ""
                
                # Process only first 10 pages for speed
                pages_to_process = min(len(pdf_reader.pages), 10)
                
                for i in range(pages_to_process):
                    page_text = pdf_reader.pages[i].extract_text() or ""
                    text += page_text + "\n"
                
                # Split into simple chunks of 1000 characters
                if text:
                    # Very simple chunking - just break into 1000 character pieces
                    chunk_size = 1000
                    for i in range(0, len(text), chunk_size):
                        chunk = text[i:i+chunk_size].strip()
                        if chunk:
                            all_chunks.append(chunk)
                    
                    print(f"Extracted chunks from {filename}")
                else:
                    print(f"No text extracted from {filename}")
                    
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
    
    return all_chunks