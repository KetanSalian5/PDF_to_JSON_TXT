#This is the update code we can able to chang the format  json or txt as per out requirements
from flask import Flask, request, jsonify, send_file
import json
import fitz
import tempfile
import os
from datetime import datetime

app = Flask(__name__)

# Create the 'tmp' directory if it doesn't exist
if not os.path.exists('tmp'):
    os.makedirs('tmp')

def convert_pdf_refined_v3(pdf_path, output_format):
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
                    
                }
            else:
                p_counter += 1  # Increment the paragraph counter
                entry = {
                    "Page": page_num + 1,
                    "Path": f"//Document/P[{page_num + 1}]/H[{h_counter}/P[{p_counter}]",
                    "Text": block_text,
                    "attributes": {
                        "LineHeight": block[3] - block[1]
                    }
                }
            content_data.append(entry)
    
    pdf_document.close()
    
    if output_format.lower() == "json":
        result = {
            "metaData": formatted_metadata,
            "content": content_data
        }
        return result
    elif output_format.lower() == "txt":
        result = ""
        for entry in content_data:
            if "Path" in entry and "Text" in entry:
                result += f"Page Number: {entry['Page']}\n {entry['Text']}\n\n"
            else:
                result += f"Page Number: {entry['Page']}\nText: {entry['Text']}\n\n"
        return result
    else:
        return "Invalid output format. Supported formats: JSON, TXT"

@app.route('/convert-pdf', methods=['POST'])
def convert_pdf_endpoint():
    if 'pdf' not in request.files:
        return jsonify({"error": "PDF file is required!"}), 400

    file = request.files['pdf']
    output_format = request.form.get("format", "json")  # Default to JSON if format parameter is not provided

    # Save the file temporarily
    file_path = "tmp/uploaded_pdf.pdf"
    file.save(file_path)
    
    # Convert the PDF using the function
    output_data = convert_pdf_refined_v3(file_path, output_format)
    
    # Cleanup: Optionally delete the temporary file after processing
    os.remove(file_path)
    
    # Return the structured data in the requested format
    if output_format.lower() == "json":
        return jsonify(output_data)
    elif output_format.lower() == "txt":
        txt_file_path = "tmp/output.txt"
        with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(output_data)
        return send_file(txt_file_path, as_attachment=True)
    else:
        return output_data, 400


if __name__ == '__main__':
    app.run(debug=True)
