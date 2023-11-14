#This is the main working code without api
import json
import fitz
from datetime import datetime
import re

def convert_pdf(pdf_path):
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
                    "Path": f"//Document/PG[{page_num + 1}]/H[{h_counter}]",
                    "Text": block_text,
                    
                }
            else:
                p_counter += 1  # Increment the paragraph counter
                entry = {
                    "Page": page_num + 1,
                    "Path": f"//Document/PG[{page_num + 1}]/H[{h_counter}]//P[{p_counter}]",
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
pdf_path = "infosys-esg-report-2021-22.pdf"

# Call the function to convert PDF to JSON
json_output = convert_pdf(pdf_path)

# Save the JSON output to a file
output_file = 'infosys-esg-report-26-10-2023-22.json'
with open(output_file, 'w', encoding='utf-8') as json_file:
    json.dump(json_output, json_file, ensure_ascii=False, indent=4)

print(f"JSON data saved to '{output_file}'.")
