#This is the code will help use to collected the data from s3 bucket url and then run in lambda combine 
import fitz
import json
from datetime import datetime
import boto3
 
 
s3_client = boto3.client("s3")
 
 
def convert_pdf(pdf_path, output_format="json"):
    try:
        pdf_document = fitz.open(pdf_path)
    except Exception as e:
        return {
            'error': f"Error opening the PDF: {e}"
        }
 
 
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
 
 
    content_data = []
 
 
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        h_counter = 0  # Counter for headers
        p_counter = 0  # Counter for paragraphs
        blocks = page.get_text("blocks")
 
 
        for idx, block in enumerate(blocks):
            block_text = block[4].replace("\n", " ").strip()
 
 
            if len(block_text.split()) < 6 and idx + 1 < len(blocks) and len(blocks[idx + 1][4].split()) > 6:
                h_counter += 1
                entry = {
                    "Page": page_num + 1,
                    "Path": f"//Document/PG[{page_num + 1}]/H[{h_counter}]",
                    "Text": block_text,
                }
            else:
                p_counter += 1
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
 
 
def pdf_to_json(event, context):
    try:
        # Extracting output_format from the query parameters, defaulting to 'json'
        query_parameters = event.get('queryStringParameters', {})
        output_format = query_parameters.get('output_format', 'json') if query_parameters else 'json'
        bucket_name = query_parameters.get('bucket_name')
        file_name = query_parameters.get('file_name')
 
 
        pdf_file_path = "/tmp/input.pdf"
        s3_client.download_file(bucket_name, file_name, pdf_file_path)
 
 
        json_output = convert_pdf(pdf_file_path, output_format)
 
 
        if output_format.lower() == "json":
            return {
                'statusCode': 200,
                'body': json.dumps(json_output)
            }
        elif output_format.lower() == "txt":
            return {
                'statusCode': 200,
                'body': json_output  # Assuming you want to return the text result as is
            }
        else:
            return {
                'statusCode': 400,  # Bad Request
                'body': "Invalid output format. Supported formats: JSON, TXT"
            }
 
 
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }