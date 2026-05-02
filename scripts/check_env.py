from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key cargada: {'✓' if api_key and api_key != 'tu_api_key_acá' else '✗ — completar .env'}")
print(f"Credentials path: {os.getenv('GOOGLE_CREDENTIALS_PATH')}")
print(f"Project root: {os.getenv('PROJECT_ROOT')}")
