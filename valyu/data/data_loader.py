import requests
import os
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

BASE_URL = 'https://api.valyu.network/v1'

def load_dataset(api_key, dataset_id, save_path='downloads'):
    try:
        """Retrieve and download data from the intermediary service to a specified file path."""
        
        print(f"Fetching dataset {dataset_id}...")

        # Transform dataset_id from orgId/datasetId to orgId:datasetId format and URL encode
        org_id, dataset_name = dataset_id.split('/')
        encoded_dataset_id = f"{org_id}%3A{dataset_name}"

        headers = {'x-api-key': api_key}
    
        # Fetch the manifest URL with the transformed dataset ID
        response = requests.get(f"{BASE_URL}/training/datasets/{encoded_dataset_id}", headers=headers)
        response.raise_for_status()

        data = response.json()
        manifest_url = data['presignedURL']
    
        # Download the manifest file
        response = requests.get(manifest_url)
        response.raise_for_status()
        manifest = response.json()

        # Create the save directory if it doesn't exist
        os.makedirs(save_path, exist_ok=True)

        # Function to download a single file
        def download_file(file_info):
            # Skip directories
            if file_info['key'].endswith('/'):
                return
            
            file_url = file_info['presignedUrl']
            file_path = os.path.join(save_path, file_info['key'])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file_response = requests.get(file_url)
            with open(file_path, 'wb') as f:
                f.write(file_response.content)

        # Download files concurrently
        with ThreadPoolExecutor() as executor:
            list(tqdm(executor.map(download_file, manifest), total=len(manifest), desc="Downloading files"))

        print(f"\nDataset downloaded successfully into {save_path}.")
    
    except Exception as e:
        raise Exception(f"Error occurred: {e}")
