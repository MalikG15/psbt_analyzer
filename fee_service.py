import requests
import os

sample_response_upon_failure = {"fastestFee": 100, "halfHourFee": 50, "hourFee": 20, "economyFee": 5, "minimumFee": 1}

# Function to read the API key from the local-secrets file
def get_api_key():
    secrets_file = 'local-secrets'
    if not os.path.exists(secrets_file):
        raise FileNotFoundError(f"The file {secrets_file} does not exist.")
    with open(secrets_file, 'r') as f:
        api_key = f.read().strip()
    return api_key

# Function to get recommended fees from mempool.space
def get_recommended_fees():
    url = 'https://mempool.space/api/v1/fees/recommended'
    api_key = get_api_key()
    headers = {
        'x-api-key': api_key  # Assuming the API key is used as a custom header; adjust if needed
    }
    try: 
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        return response.json()
    except:
        return sample_response_upon_failure

# Example usage (can be removed if this is used as a module)
if __name__ == "__main__":
    try:
        fees = get_recommended_fees()
        print(fees)
    except Exception as e:
        print(f"Error: {e}")