'''In this code I get the data from the s3 bucket and We convert the output  in the url formate that save the 
data as per our need like Json Or Txt formate type then we push this in lambda '''

import fitz
import json
from datetime import datetime
import boto3
 
s3_client = boto3.client("s3")
 
# Define your S3 bucket name where you want to store the output files.
output_bucket_name = "vinayagam-testing-esgds"
 
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
        # Extracting output_format, bucket_name, and file_name from the query parameters.
        query_parameters = event.get('queryStringParameters', {})
        output_format = query_parameters.get('output_format', 'json') if query_parameters else 'json'
        bucket_name = query_parameters.get('bucket_name')
        file_name = query_parameters.get('file_name')
 
        pdf_file_path = "/tmp/input.pdf"
        s3_client.download_file(bucket_name, file_name, pdf_file_path)
 
        json_output = convert_pdf(pdf_file_path, output_format)
 
        if output_format.lower() == "json":
            # Save the JSON result to S3
            output_key = f"{file_name.replace('.pdf', '')}.json"
            s3_client.put_object(Bucket=output_bucket_name, Key=output_key, Body=json.dumps(json_output))
 
            # Generate a pre-signed URL for the JSON file
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': output_bucket_name, 'Key': output_key},
                ExpiresIn=600  # URL expiration time (adjust as needed)
            )
 
            return {
                'statusCode': 200,
                'body': json.dumps({'pre_signed_url': presigned_url})
            }
        elif output_format.lower() == "txt":
            # Save the text result to S3
            output_key = f"{file_name.replace('.pdf', '')}.txt"
            s3_client.put_object(Bucket=output_bucket_name, Key=output_key, Body=json_output)
 
            # Generate a pre-signed URL for the text file
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': output_bucket_name, 'Key': output_key},
                ExpiresIn=600  # URL expiration time (adjust as needed)
            )
 
            return {
                'statusCode': 200,
                'body': json.dumps({'pre_signed_url': presigned_url})
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