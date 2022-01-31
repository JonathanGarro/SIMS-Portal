import os
from dotenv import load_dotenv
load_dotenv()

print("Trying .env connection:")
print( os.environ.get("FLASK_APP_API_KEY") )