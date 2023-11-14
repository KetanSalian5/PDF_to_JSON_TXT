import json
import fitz
from datetime import datetime
from PIL import Image
from io import BytesIO
import pytesseract
import re

# Path to the Tesseract executable (change this according to your installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def perform_ocr(image_bytes):
    # Convert raw image data to PIL Image
    pil_image = Image.open(BytesIO(image_bytes))

    # Perform OCR using pytesseract
    image_text = pytesseract.image_to_string(pil_image)

    return image_text

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

    # Initialize counters
    h_counter = 0  # Counter for headers
    p_counter = 0  # Counter for paragraphs
    img_counter = 0  # Counter for images

    # Initialize data structures
    content_data = []

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)

        blocks = page.get_text("blocks")
        for idx, block in enumerate(blocks):
            block_text = block[4].replace("\n", " ").strip()  # Text content

            entry = {
                "Page": page_num + 1,
                "Text": block_text,
                "attributes": {
                    "LineHeight": block[3] - block[1]
                }
            }

            # Check if this block is a header
            if len(block_text.split()) < 6 and idx + 1 < len(blocks) and len(blocks[idx + 1][4].split()) > 6:
                h_counter += 1
                entry["Type"] = "Header"
                entry["Path"] = f"//Document/PG[{page_num + 1}]/H[{h_counter}]"
            else:
                p_counter += 1
                entry["Type"] = "Paragraph"
                entry["Path"] = f"//Document/PG[{page_num + 1}]/P[{p_counter}]"

            content_data.append(entry)

            # Extract images from the block
            img_list = page.get_images(full=True)

            # Iterate through each image in the block
            for img_index, img in enumerate(img_list):
                try:
                    # Extract image data
                    img_base = pdf_document.extract_image(img[0])
                    image_bytes = img_base["image"]

                    # Perform OCR on the image using pytesseract
                    image_text = pytesseract.image_to_string(pil_image)

                    # Add the page number as a prefix to the image text
                    text = f"Page {page_num + 1}, Image {img_index + 1} OCR:\n{image_text}\n"

                    # # Create a separate entry for the image
                    # img_counter += 1
                    # img_entry = {
                    #     "Page": page_num + 1,
                    #     "Type": "Image",
                    #     "Path": f"//Document/PG[{page_num + 1}]/IMG[{img_counter}]",
                    #     "Text": text
                    # }

                    # Add the image entry to the content data
                    #content_data.append(img_entry)

                except Exception as e:
                    # Handle errors silently
                    pass

    pdf_document.close()

    result = {
        "metaData": formatted_metadata,
        "content": content_data
    }
    return result

# Example usage
pdf_path = "infosys-esg-report-2022-23.pdf"
json_output = convert_pdf(pdf_path)

# Save the JSON output to a file
output_file = 'infosys-esg-report-202-with-ocr.json'
with open(output_file, 'w', encoding='utf-8') as json_file:
    json.dump(json_output, json_file, ensure_ascii=False, indent=4)

print(f"JSON data with OCR saved to '{output_file}'.")
