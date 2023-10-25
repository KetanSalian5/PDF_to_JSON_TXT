from flask import Flask, request, jsonify
import fitz
import json
import os
from datetime import datetime

app = Flask(__name__)

if not os.path.exists('tmp'):
    os.makedirs('tmp')


def convert_pdf_refined_v3(pdf_path):
    try:
        pdf_document = fitz.open(pdf_path)
    except Exception as e:
        return f"Error opening the PDF: {e}"

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
                    "Path": f"//Document/H[{h_counter}]",
                    "Text": block_text,
                    "TextSize": block[6]
                }
            else:
                p_counter += 1  # Increment the paragraph counter
                entry = {
                    "Page": page_num + 1,
                    "Path": f"//Document/P[{p_counter}]",
                    "Text": block_text,
                    "TextSize": block[6],
                    "attributes": {
                        "LineHeight": block[3] - block[1]
                    }
                }
            content_data.append(entry)
    
    pdf_document.close()
    
    return {
        "metaData": formatted_metadata,
        "content": content_data
    }
    # Your PDF-to-JSON conversion code here (the code you provided)

@app.route('/convert_tes', methods=['POST'])
def upload_and_convert():
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400  # 400 Bad Request

        file = request.files['file']

        # Check if the file has an allowed extension (PDF)
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400  # 400 Bad Request

        if file:
            # Save the uploaded file temporarily
            temp_pdf_path = 'tmp/temp.pdf'  # Save in the 'tmp' directory
            file.save(temp_pdf_path)

            # Convert the PDF to JSON
            json_data = convert_pdf_refined_v3(temp_pdf_path)

            # Clean up the temporary file
            os.remove(temp_pdf_path)

            return jsonify(json_data), 200  # 200 OK

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500  # 500 Internal Server Error

if __name__ == '__main__':
    app.run(debug=True)