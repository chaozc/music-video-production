#!/usr/bin/env python3
"""
Upload a video to YouTube via the YouTube Data API v3.

Usage:
  python upload.py --video video.mp4 --title "My Video" --description "Desc" \
    --tags "tag1,tag2" --category 10 --privacy private

  # With thumbnail and playlist
  python upload.py --video video.mp4 --title "My Video" \
    --thumbnail thumb.jpg --playlist "My Playlist"

  # Scheduled publish
  python upload.py --video video.mp4 --title "My Video" \
    --privacy private --schedule "2026-04-01T12:00:00Z"

Environment:
  YOUTUBE_CLIENT_SECRETS  Path to OAuth2 client_secrets.json (required on first auth)
  YOUTUBE_TOKEN_FILE      Path to saved token (default: ~/.youtube-upload-token.json)
"""
import argparse
import json
import os
import sys
import time

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print(
        "ERROR: Required packages not installed. Run:\n"
        "  pip install google-api-python-client google-auth-oauthlib",
        file=sys.stderr,
    )
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

DEFAULT_TOKEN_FILE = os.path.expanduser("~/.youtube-upload-token.json")


def parse_args():
    p = argparse.ArgumentParser(description="Upload video to YouTube")
    p.add_argument("--video", required=True, help="Path to video file")
    p.add_argument("--title", required=True, help="Video title (max 100 chars)")
    p.add_argument("--description", default="", help="Video description (max 5000 chars)")
    p.add_argument("--tags", default="", help="Comma-separated tags")
    p.add_argument("--category", default="10", help="YouTube category ID (default: 10 Music)")
    p.add_argument("--privacy", default="private", choices=["public", "unlisted", "private"],
                    help="Privacy status (default: private)")
    p.add_argument("--thumbnail", help="Path to thumbnail image (jpg/png, max 2MB)")
    p.add_argument("--playlist", help="Playlist name or ID to add video to")
    p.add_argument("--schedule", help="ISO 8601 datetime for scheduled publish (requires private)")
    p.add_argument("--language", default="en", help="Video language (default: en)")
    p.add_argument("--made-for-kids", action="store_true", help="Mark as made for kids")
    p.add_argument("--output-json", help="Save upload result to JSON file")
    return p.parse_args()


def get_credentials():
    """Load or create OAuth2 credentials."""
    token_file = os.environ.get("YOUTUBE_TOKEN_FILE", DEFAULT_TOKEN_FILE)
    creds = None

    # Load existing token
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # Refresh or create new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(Request())
        else:
            secrets_file = os.environ.get("YOUTUBE_CLIENT_SECRETS")
            if not secrets_file:
                print(
                    "ERROR: YOUTUBE_CLIENT_SECRETS env not set. "
                    "Set it to the path of your OAuth2 client_secrets.json",
                    file=sys.stderr,
                )
                sys.exit(1)
            if not os.path.exists(secrets_file):
                print(f"ERROR: Client secrets not found: {secrets_file}", file=sys.stderr)
                sys.exit(1)

            print("🔐 Opening browser for OAuth consent...")
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token
        with open(token_file, "w") as f:
            f.write(creds.to_json())
        print(f"💾 Token saved: {token_file}")

    return creds


def upload_video(youtube, args):
    """Upload video and return video ID."""
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    body = {
        "snippet": {
            "title": args.title[:100],
            "description": args.description[:5000],
            "tags": tags,
            "categoryId": args.category,
            "defaultLanguage": args.language,
        },
        "status": {
            "privacyStatus": args.privacy,
            "selfDeclaredMadeForKids": args.made_for_kids,
        },
    }

    if args.schedule:
        body["status"]["publishAt"] = args.schedule
        if args.privacy != "private":
            print("⚠️  Scheduled publish requires private privacy; overriding to private")
            body["status"]["privacyStatus"] = "private"

    media = MediaFileUpload(args.video, mimetype="video/mp4", resumable=True, chunksize=10 * 1024 * 1024)

    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    print(f"📤 Uploading: {args.video}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"   {pct}% uploaded", end="\r")

    video_id = response["id"]
    print(f"\n✅ Uploaded: https://youtu.be/{video_id}")
    return video_id


def set_thumbnail(youtube, video_id, thumbnail_path):
    """Set custom thumbnail for video."""
    if not os.path.exists(thumbnail_path):
        print(f"⚠️  Thumbnail not found: {thumbnail_path}", file=sys.stderr)
        return False

    size_mb = os.path.getsize(thumbnail_path) / 1024 / 1024
    if size_mb > 2:
        print(f"⚠️  Thumbnail too large ({size_mb:.1f}MB > 2MB limit)", file=sys.stderr)
        return False

    mime = "image/jpeg" if thumbnail_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    media = MediaFileUpload(thumbnail_path, mimetype=mime)

    youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
    print(f"🖼️  Thumbnail set: {thumbnail_path}")
    return True


def find_or_create_playlist(youtube, name):
    """Find playlist by name or create it. Returns playlist ID."""
    # Check if name looks like a playlist ID
    if name.startswith("PL") and len(name) > 10:
        return name

    # Search existing playlists
    playlists = youtube.playlists().list(part="snippet", mine=True, maxResults=50).execute()
    for pl in playlists.get("items", []):
        if pl["snippet"]["title"].lower() == name.lower():
            print(f"📂 Found playlist: {pl['snippet']['title']}")
            return pl["id"]

    # Create new playlist
    body = {
        "snippet": {"title": name, "description": ""},
        "status": {"privacyStatus": "private"},
    }
    result = youtube.playlists().insert(part="snippet,status", body=body).execute()
    print(f"📂 Created playlist: {name}")
    return result["id"]


def add_to_playlist(youtube, playlist_id, video_id):
    """Add video to playlist."""
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {"kind": "youtube#video", "videoId": video_id},
        }
    }
    youtube.playlistItems().insert(part="snippet", body=body).execute()
    print(f"✅ Added to playlist")


def main():
    args = parse_args()

    # Validate
    if not os.path.exists(args.video):
        print(f"ERROR: Video not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    size_mb = os.path.getsize(args.video) / 1024 / 1024
    print(f"📁 Video: {args.video} ({size_mb:.1f} MB)")
    print(f"📝 Title: {args.title}")
    print(f"🔒 Privacy: {args.privacy}")
    if args.schedule:
        print(f"📅 Scheduled: {args.schedule}")
    print()

    # Auth
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    # Upload
    video_id = upload_video(youtube, args)

    # Thumbnail
    if args.thumbnail:
        set_thumbnail(youtube, video_id, args.thumbnail)

    # Playlist
    if args.playlist:
        playlist_id = find_or_create_playlist(youtube, args.playlist)
        add_to_playlist(youtube, playlist_id, video_id)

    # Save result
    result = {
        "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}",
        "title": args.title,
        "privacy": args.privacy,
        "source_video": os.path.basename(args.video),
    }
    if args.playlist:
        result["playlist"] = args.playlist
    if args.schedule:
        result["schedule"] = args.schedule

    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"📝 Result saved: {args.output_json}")

    # Print JSON to stdout for agent to capture
    print(f"\n{json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
