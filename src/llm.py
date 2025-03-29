import requests
import config
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

# Get API key from environment
HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = f"https://api-inference.huggingface.co/models/{config.HF_MODEL_NAME}"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

def query_llm(prompt: str) -> str:
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.3,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx/5xx)
        output = response.json()

        if isinstance(output, list) and 'generated_text' in output[0]:
            return output[0]['generated_text']
        elif isinstance(output, dict) and 'generated_text' in output:
            return output['generated_text']
        else:
            return str(output)

    except requests.exceptions.RequestException as e:
        return f"[Error] Request failed: {str(e)}"
    except Exception as e:
        return f"[Error] Unexpected failure: {str(e)}"

