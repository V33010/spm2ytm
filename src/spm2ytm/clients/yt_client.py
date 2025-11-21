from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube"]

ROOT_DIR = Path(__file__).resolve().parents[2]
OAUTH_JSON = ROOT_DIR / "oauth.json"
CLIENT_SECRET = ROOT_DIR / "client_secret.json"


def get_youtube_client():
    creds = None

    if OAUTH_JSON.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(OAUTH_JSON), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)

        # Use run_local_server instead of run_console
        creds = flow.run_local_server(port=0)

        with open(OAUTH_JSON, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)
