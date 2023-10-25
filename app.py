#This is code went to prodution UAT for testing pdf extraction to Json 
from flask import Flask, request, jsonify
import json
import fitz #Pymupdf
import tempfile
import os
from datetime import datetime

app = Flask(__name__)


# Create the 'tmp' directory if it doesn't exist
if not os.path.exists('tmp'):
    os.makedirs('tmp')

def convert_pdf_refined_v3(pdf_path):
    try:
        pdf_document = fitz.open(pdf_path)
    except Exception as e:
        return f"Error opening the PDF: {e}"
    
    # return pdf_document

    # Extract and format metadata
    metaData = pdf_document.metadata
    formatted_metadata = {}
    for key, value in metaData.items():
        formatted_value = value
        if "date" in key.lower() and value:
            try:
                formatted_value = datetime.strptime(value[2:16], '%Y%m%d%H%M%S').strftime('%m/%d/%y, %I:%M:%S %p')
            except ValueError:
                pass
        formatted_metadata[key] = formatted_value
        
    

    # Extract content and organize into sections based on headers and paragraphs
    content_data = []
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        
        h_counter = 0  # Counter for headers
        p_counter = 0  # Counter for paragraphs
        
        blocks = page.get_text("blocks")
        for idx, block in enumerate(blocks):
            block_text = block[4].replace("\n", " ").strip()  # Text content
            
            # If this block is possibly a header, check the next block
            # Headers are usually shorter and followed by longer paragraphs
            if len(block_text.split()) < 6 and idx + 1 < len(blocks) and len(blocks[idx + 1][4].split()) > 6:
                h_counter += 1  # Increment the header counter
                entry = {
                    "Page": page_num + 1,
                    "Path": f"//Document/PG[{page_num + 1}]/H[{h_counter}]",
                    "Text": block_text,
                    
                }
            else:
                p_counter += 1  # Increment the paragraph counter
                entry = {
                    "Page": page_num + 1,
                    "Path": f"//Document/PG[{page_num + 1}]/H[{h_counter}]/P[{p_counter }]",
                    "Text": block_text,
                    "attributes": {
                        "LineHeight": block[3] - block[1]
                    }
                }
            content_data.append(entry)
    
    pdf_document.close()
    
    result = {
        "metaData": formatted_metadata,
        "content": content_data
    }
    return result

@app.route('/convert-pdf', methods=['POST'])
def convert_pdf_endpoint():
    if 'pdf' not in request.files:
        return jsonify({"error": "PDF file is required!"}), 400

    file = request.files['pdf']

    
    # Save the file temporarily
    file_path = "tmp/uploaded_pdf.pdf"
    file.save(file_path)
    
    # Convert the PDF using the function
    json_output = convert_pdf_refined_v3(file_path)
    
    # Cleanup: Optionally delete the temporary file after processing
   # os.remove(file_path)
    
    # Return the structured JSON data
    # return jsonify(json_output)
    return json_output

if __name__ == '__main__':
    app.run(debug=True)
