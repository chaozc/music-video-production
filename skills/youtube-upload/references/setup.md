# YouTube Upload Setup Guide

## Google Cloud Project Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Navigate to **APIs & Services > Library**
4. Search for **YouTube Data API v3** and enable it
5. Navigate to **APIs & Services > Credentials**
6. Click **Create Credentials > OAuth 2.0 Client ID**
7. Application type: **Desktop app**
8. Download the JSON file as `client_secrets.json`

## Environment

Set the path to your credentials:

```bash
export YOUTUBE_CLIENT_SECRETS=/path/to/client_secrets.json
```

## First-time Authentication

On first run, the upload script will:
1. Open a browser window for Google OAuth consent
2. Ask you to grant YouTube upload permissions
3. Save the refresh token to `~/.youtube-upload-token.json`

Subsequent runs use the saved token automatically. If the token expires or is revoked, delete the token file and re-authenticate.

## Required OAuth Scopes

- `https://www.googleapis.com/auth/youtube.upload` — upload videos
- `https://www.googleapis.com/auth/youtube` — manage playlists, thumbnails

## Quota

YouTube Data API v3 has a default quota of **10,000 units/day**.

| Operation | Cost |
|-----------|------|
| Upload video | 1,600 units |
| Set thumbnail | 50 units |
| Add to playlist | 50 units |
| Update metadata | 50 units |

With the default quota, you can upload approximately **6 videos per day**. Request a quota increase via Google Cloud Console if needed.

## Verified Account

Custom thumbnails require a verified YouTube account:
1. Go to [YouTube verification](https://www.youtube.com/verify)
2. Verify via phone number
3. Wait up to 24 hours for verification to take effect
