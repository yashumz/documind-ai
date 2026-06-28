# test_s3_handler.py
import os
from dotenv import load_dotenv
from ingestion.s3_handler import get_s3_client

load_dotenv()

s3     = get_s3_client()
bucket = os.getenv("S3_BUCKET_NAME")

response = s3.list_objects_v2(Bucket=bucket)
count    = response["KeyCount"]

print(f"✅ S3 handler working — bucket has {count} objects")
print(f"✅ Bucket: {bucket}")