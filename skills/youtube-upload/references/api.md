# YouTube Data API v3 Reference

## Upload Endpoint

```
POST https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status
```

### Request Body (snippet)

```json
{
  "snippet": {
    "title": "Video Title (max 100 chars)",
    "description": "Video description (max 5000 chars)",
    "tags": ["tag1", "tag2"],
    "categoryId": "10",
    "defaultLanguage": "en"
  },
  "status": {
    "privacyStatus": "private",
    "publishAt": "2026-03-17T12:00:00Z",
    "selfDeclaredMadeForKids": false
  }
}
```

### Category IDs

| ID | Category |
|----|----------|
| 1 | Film & Animation |
| 10 | Music |
| 15 | Pets & Animals |
| 20 | Gaming |
| 22 | People & Blogs |
| 24 | Entertainment |
| 25 | News & Politics |
| 26 | Howto & Style |
| 27 | Education |
| 28 | Science & Technology |

## Thumbnail Endpoint

```
POST https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId=<VIDEO_ID>
```

Upload a JPEG or PNG image (max 2MB, recommended 1280x720).

## Playlist Endpoint

### Create Playlist

```
POST https://www.googleapis.com/youtube/v3/playlists?part=snippet,status
```

### Add to Playlist

```
POST https://www.googleapis.com/youtube/v3/playlistItems?part=snippet
```

```json
{
  "snippet": {
    "playlistId": "<PLAYLIST_ID>",
    "resourceId": {
      "kind": "youtube#video",
      "videoId": "<VIDEO_ID>"
    }
  }
}
```

## Python Client Library

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

credentials = Credentials.from_authorized_user_file("~/.youtube-upload-token.json")
youtube = build("youtube", "v3", credentials=credentials)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": "My Video",
            "description": "Description",
            "tags": ["tag1", "tag2"],
            "categoryId": "10"
        },
        "status": {
            "privacyStatus": "private"
        }
    },
    media_body=MediaFileUpload("video.mp4", mimetype="video/mp4", resumable=True)
)
response = request.execute()
video_id = response["id"]
```

## Rate Limits

- Default quota: 10,000 units/day
- Upload: 1,600 units per video
- Most read operations: 1 unit
- Quota resets at midnight Pacific Time
