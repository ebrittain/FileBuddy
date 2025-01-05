import os
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Path to the .env file
ENV_FILE = ".env"


def is_valid_path(path):
    """Validate that the path does not contain invalid sequences like '..'."""
    return ".." not in path and not os.path.isabs(path)


def get_secret_key():
    # Check if the key exists in environment variables
    secret_key = os.getenv('FLASK_SECRET_KEY')

    if secret_key:
        return secret_key

    # Generate a new key if none exists
    secret_key = Fernet.generate_key().decode()  # Convert bytes to string

    # Append the key to the .env file
    with open(ENV_FILE, 'a') as env_file:
        env_file.write(f"FLASK_SECRET_KEY={secret_key}\n")

    print("A new secret key has been generated and added to .env.")
    return secret_key
