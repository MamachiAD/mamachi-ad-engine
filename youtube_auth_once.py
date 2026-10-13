"""Run ONCE on your own computer (it opens a browser). Needs client_secrets.json from Google Cloud.
Copy the printed JSON into the GitHub secret YOUTUBE_TOKEN_JSON.
Set your OAuth consent screen to 'In production', otherwise Google expires the token after 7 days."""
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", ["https://www.googleapis.com/auth/youtube.upload"])
creds = flow.run_local_server(port=0)
print(creds.to_json())
