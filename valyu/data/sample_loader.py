import requests
import zipfile
from io import BytesIO
import os

BASE_URL = 'https://api.valyu.network/v1'

def load_dataset_samples(dataset_identifier: str, save_path: str = 'downloads') -> bool:
    """
    Retrieve and download sample data for a dataset.

    Args:
        dataset_identifier (str): A string in the format 'org_id/dataset_name'.
            For example: 'Valyu/papers'
        save_path (str, optional): Directory to save the downloaded samples. 
            Defaults to 'downloads'.

    Raises:
        ValueError: If the dataset_identifier is not in the correct format.
        requests.exceptions.RequestException: If there's an error fetching the data.
    """
    try:
        print(f"Fetching samples...")
        
        # Validate and unpack the dataset identifier
        if '/' not in dataset_identifier:
            raise ValueError("dataset_identifier must be in the format 'org_id/dataset_name'")
        org_id, dataset_name = dataset_identifier.split('/', 1)
        
        # Construct the API request
        params = {
            "orgId": org_id,
            "datasetName": dataset_name
        }
        
        # Fetch the presigned URL for samples
        response = requests.get(f"{BASE_URL}/training/samples", params=params)
        response.raise_for_status()
        data = response.json()
        presigned_url = data['presigned_url']
        
        # Download the zip file
        try:
            response = requests.get(presigned_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error downloading the zip file: {e}")
            return False
        
        # Extract the contents
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            for file_info in zip_ref.infolist():
                if not file_info.filename.startswith('__MACOSX'):
                    zip_ref.extract(file_info, save_path)
        
        # Remove any empty directories
        for root, dirs, files in os.walk(save_path, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
        
        print(f"Sample data downloaded and extracted successfully to {save_path}.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sample data: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
