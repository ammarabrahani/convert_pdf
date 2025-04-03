from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from pdf2image import convert_from_bytes
import os
import uuid
import logging
import boto3
from dotenv import load_dotenv
from mangum import Mangum



# ✅ Load Environment Variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
handler = Mangum(app)



# ✅ AWS S3 Configuration
AWS_ACCESS_KEY_ID = "ASIA356KBJWWNLSDXBUW"
AWS_SECRET_ACCESS_KEY = "jg+780fyiZx3XBs9TtDKX0p5JGa2zM/tAEYIF9tF"
AWS_S3_BUCKET_NAME = "scalablebuckets"
AWS_REGION = "us-east-1"
AWS_SESSION_TOKEN = "IQoJb3JpZ2luX2VjEHkaCXVzLXdlc3QtMiJHMEUCIEJhY2nRZ7MSqxdLNYyp1Lciy+rju16Sc6KSx8nlxbYXAiEAuwqrMU+Q846Q5ELxRg61Jye7h0unGUJ0RPUG3qF6uiYqvQII4v//////////ARAAGgw4MjAyMjU1OTI3NDgiDEcXVm8dKAJBBsF3ySqRAgAefqKina63R/kIg29aMl/Wgjn0aT8yAz5f+wYpOQuqb5rgbhx3pZ1amjdQj04YSbesLvst/V2OTzph9l71kTZZEfAzAwyFwoX8A31jzV+c7RYLQDEg/R4kohgqjfh2g4mRfDd7fIje6KpSkXGnIo/syGtMQxr00wg2gjDcvwMbVLkoNpWQGadLWifOh6VoE4CfTpZCtQLltg68sYUytVSu1iNj9W80Xk2dbPVBxLxbGzdrIXpMNelRbxW99EDOHRJ89tEfN3R2AdqTs6KCdjBNwXCB/iHa92YwIO+ELGZKQMiF1g6kU7c3NLSoY4t02AzJtPzcrkMW+wZDGpP8Ve2WwUCWROJ8/QPn6b/DXqL/SDCDure/BjqdARvfZfBII1VyAAyuvaVQy1R2QIFsRW2pdsQKn47zrFbRD2sv+Jh7LoxAZq3YhP80fEEPY4rZ6VHVa+GF/81yPmaFScmDhiGETnqLeNKJRtyEeFeMucvVWEdtBkCHueP0FF+ElSbsmbi0Nb1tGT7opyrealLu71sIUUD5wi0Qu9kYEAJJAt+imKqb1Rgulp0KMiBakzjbXzKdt6TqJHg="

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME]):
    raise RuntimeError("AWS credentials or bucket name are missing! Check your .env file.")

# ✅ Poppler Path (PDF to Image Converter)
POPPLER_PATH = r"C:\poppler\Library\bin"  # Windows Example
IMAGE_DIR = "static/images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# ✅ Serve Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ Initialize S3 Client
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI on AWS!"}


@app.post("/convert-pdf/")
async def convert_pdf(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        if not pdf_bytes:
            raise HTTPException(status_code=400, detail="Invalid PDF file uploaded.")

        images = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)
        if not images:
            raise HTTPException(status_code=500, detail="PDF conversion failed.")

        image_urls = []
        for i, image in enumerate(images):
            image_filename = f"{uuid.uuid4()}_page{i+1}.png"
            temp_image_path = os.path.join(IMAGE_DIR, image_filename)

            image.save(temp_image_path, format="PNG")

            if not os.path.exists(temp_image_path):
                raise FileNotFoundError(f"File not found: {temp_image_path}")

            s3_key = f"pdf_images/{image_filename}"
            s3_client.upload_file(temp_image_path, AWS_S3_BUCKET_NAME, s3_key, ExtraArgs={"ContentType": "image/png"})

            image_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
            image_urls.append(image_url)

            os.remove(temp_image_path)

        return {"filename": file.filename, "image_urls": image_urls, "message": "PDF converted and uploaded to S3 successfully."}

    except HTTPException as he:
        return {"error": he.detail}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
    
