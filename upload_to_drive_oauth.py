import os
import argparse

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Für Upload in deinen Drive reicht drive.file normalerweise.
# Wenn du Probleme mit Ordnerzugriff hast, nimm "drive".
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_creds(credentials_json: str, token_json: str) -> Credentials:
    creds = None
    if os.path.exists(token_json):
        creds = Credentials.from_authorized_user_file(token_json, SCOPES)

    # Token abgelaufen? -> automatisch refreshen (wenn refresh_token vorhanden)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # Noch keine Credentials? -> interaktives Login (einmalig)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_json, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_json, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds

def upload_file(file_path: str, folder_id: str | None, credentials_json: str, token_json: str):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

    creds = get_creds(credentials_json, token_json)
    service = build("drive", "v3", credentials=creds)

    file_name = os.path.basename(file_path)
    metadata = {"name": file_name}
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)

    request = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,name"
    )

    print(f"Uploading {file_name} ({os.path.getsize(file_path)/1024/1024:.1f} MB) ...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Fortschritt: {int(status.progress() * 100)}%")

    print("✅ Upload fertig")
    print("File ID:", response["id"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="weights/Encoder_Interpolation_CE_PeriodicSum_2000.pt", help="Pfad zur .pt Datei")
    ap.add_argument("--folder_id", default="1AsGAoGrbRq9hpk8Moas3JxAozoJlMtTf", help="Optional: Zielordner-ID in Drive")
    ap.add_argument("--credentials", default="credentials.json", help="OAuth client secrets JSON")
    ap.add_argument("--token", default="token.json", help="Token cache (wird erstellt)")
    args = ap.parse_args()

    upload_file(args.file, args.folder_id, args.credentials, args.token)

if __name__ == "__main__":
    main()
