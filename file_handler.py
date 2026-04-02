from rapidfuzz import fuzz, process
import pandas as pd
import io
import tempfile
from google.cloud import storage
import datetime
import os
import pytz

bucket_name = "llm_lite"
credentials_path= "helpinghands-8711e-8d9914c4db30.json"
folder_path = "Chatbot-data"

def minutes_to_hhmmss(minutes):
    if pd.isna(minutes):
        return None
    return str(datetime.timedelta(minutes=int(minutes)))


def handle_attendance_data(df):
    ist = pytz.timezone("Asia/Kolkata")
    df["first_clock_in"] = (
        pd.to_datetime(df["first_clock_in"], unit="s", errors="coerce")
        .dt.tz_localize("UTC")      # assume input is in UTC
        .dt.tz_convert(ist)   
        .dt.tz_localize(None)       # convert to IST
    )

    df["last_clock_out"] = (
        pd.to_datetime(df["last_clock_out"], unit="s", errors="coerce")
        .dt.tz_localize("UTC")
        .dt.tz_convert(ist)
        .dt.tz_localize(None) 
    )

    df["total_minutes"] = df["total_minutes"].apply(minutes_to_hhmmss)

    return df

def df_to_csv(data):
    """Convert data to CSV format"""
    return data.to_csv(index=False).encode("utf-8")

def df_to_excel(data):
    """Convert data to Excel format"""
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            data.to_excel(writer, index=False, sheet_name="Sheet1")
        return buffer.getvalue()


def generate_filename(file_type, folder_path):
    """Generate a unique filename with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    extension_map = {
        'csv': 'csv',
        'excel': 'xlsx',
        'xlsx': 'xlsx',
        'xls': 'xlsx',
    }

    extension = extension_map.get(file_type, 'csv')
    filename = f"data_{timestamp}.{extension}"
    print(folder_path)
    if folder_path: 
        folder_path = folder_path.strip('/')
        if folder_path:
            filename = f"{folder_path}/{filename}"
    return filename

def generate_download_signed_url(bucket, blob_name, expiration_minutes=15, force_download=True, custom_filename=None):
    """Generate a signed URL - works with older google-cloud-storage versions"""
    blob = bucket.blob(blob_name)
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration_minutes)
    
    # For older versions, we'll set metadata on the blob to control download behavior
    if force_download:
        download_filename = custom_filename or os.path.basename(blob_name)
        
        # Set blob metadata to force download (this works with older library versions)
        blob.content_disposition = f'attachment; filename="{download_filename}"'
        blob.content_type = 'application/octet-stream'
        blob.patch()  # Update the blob metadata
    
    # Generate standard signed URL
    return blob.generate_signed_url(
        expiration=expiration,
        method='GET'
    )
    
def upload_to_gcp_and_get_signed_url(data, file_type, custom_download_filename=None, force_download=True):
    """
    Main function to process user query, convert data, upload to GCP, and generate pre-signed URL
    
    Args:
        data: List of dictionaries or pandas DataFrame
        file_type: "csv" or "excel"/"xlsx"/"xls"
        custom_download_filename: Optional custom download filename
        force_download: Force download instead of inline preview
    
    Returns:
        dict: Contains success status, signed_url, error (if any)
    """
    try:
        data = pd.DataFrame(data)
        required_cols = {"first_clock_in", "last_clock_out", "total_minutes"}
        if required_cols.issubset(data.columns):
            data = handle_attendance_data(data)

        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # Pick content + content_type
        if file_type == 'csv':
            file_content = df_to_csv(data)
            upload_type = "text/csv"
        elif file_type in ["excel", "xls", "xlsx"]:
            file_content = df_to_excel(data)
            upload_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            return {"success": False, "error": f"Unsupported file_type: {file_type}"}
        
        # Generate filename
        filename = generate_filename(file_type, folder_path)
        
        blob = bucket.blob(filename)

        if force_download:
            download_filename = custom_download_filename or os.path.basename(filename)
            blob.content_disposition = f'attachment; filename="{download_filename}"'

        blob.upload_from_string(file_content, content_type=upload_type)

        expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        signed_url = blob.generate_signed_url(
            expiration=expiration,
            method='GET'
        )
        
        return {
            'success': True,
            'signed_url': signed_url,
            'filename': filename,
            'file_type': file_type
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

