import os
from pypdf import PdfReader

def process_documents(documents_folder):
    """
    Simple and fast document processing function.
    
    Args:
        documents_folder: Folder containing PDF documents
        
    Returns:
        list: List of text chunks
    """
    all_chunks = []
    
    # Check if folder exists
    if not os.path.exists(documents_folder):
        print(f"Documents folder {documents_folder} does not exist")
        return all_chunks
    
    # Process each PDF file
    for filename in os.listdir(documents_folder):
        if filename.endswith('.pdf'):
            print(f"Processing {filename}...")
            file_path = os.path.join(documents_folder, filename)
            
            try:
                # Simple text extraction
                pdf = PdfReader(file_path)
                text = ""
                
                # Extract text from each page
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                
                # Simple chunking - break by paragraphs first, then by size if needed
                paragraphs = text.split('\n\n')
                
                for para in paragraphs:
                    if para.strip():  # Skip empty paragraphs
                        # If paragraph is too large, break it into smaller chunks
                        if len(para) > 1000:
                            for i in range(0, len(para), 1000):
                                chunk = para[i:i+1000].strip()
                                if chunk:
                                    all_chunks.append(chunk)
                        else:
                            all_chunks.append(para.strip())
                
                print(f"Extracted {len(paragraphs)} paragraphs from {filename}")
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
    
    print(f"Total chunks extracted: {len(all_chunks)}")
    return all_chunks
