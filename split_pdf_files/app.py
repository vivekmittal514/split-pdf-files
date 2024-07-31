import os
import boto3
from botocore.exceptions import ClientError
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO


# Initialize the S3 client
s3 = boto3.client('s3')

# Function to split the PDF file
def lambda_handler(event, context):

    # Get the key name from the event
    key = event['detail']['object']['key']

    # Get the source and destination bucket names from the environment variables
    source_bucket_name = os.environ.get('SOURCE_BUCKET')
    dest_bucket_name = os.environ.get('DESTINATION_BUCKET')

    # Download the PDF file from the source S3 bucket
    try:
        response = s3.get_object(Bucket=source_bucket_name, Key=key)
        pdf_file = BytesIO(response['Body'].read())

    except Exception as e:
        print(f"Error downloading PDF file: {e}")
        return

    # Open the PDF file
    pdf_reader = PdfReader(pdf_file)

    # Split the PDF into individual pages
    for page_num in range(len(pdf_reader.pages)):
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf_reader.pages[page_num])

        output_filename = f"{key.split('/')[-1].split('.')[0]}_{page_num}.pdf"

        # Create a temporary file to store the split PDF
        with open(f"/tmp/{output_filename}", 'wb') as out:
            pdf_writer.write(out)

        # Upload the split PDF to the destination S3 bucket
        dest_key = f"{output_filename}"
        try:
            s3.upload_file(f"/tmp/{output_filename}", dest_bucket_name, dest_key)
        except Exception as e:
            print(f"Error uploading file {output_filename} to S3: {e}")

        # Remove the temporary file
        os.remove(f"/tmp/{output_filename}")

    return {
        'statusCode': 200,
        'body': 'PDF file split and uploaded successfully'
    }
