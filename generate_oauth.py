from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def main():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=8080)

    with open("oauth.json", "w") as f:
        f.write(creds.to_json())

    print("oauth.json created successfully!")


if __name__ == "__main__":
    main()
