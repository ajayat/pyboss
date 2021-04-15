import os

from googleapiclient.discovery import build


def search(query: str, n=1) -> dict:
    """
    Search video on youtube matching the query
    """
    youtube = build("youtube", "v3", developerKey=os.getenv("API_DEVELOPER_KEY"))
    response = (
        youtube.search()
        .list(part="snippet", q=query, type="video", maxResults=n)
        .execute()
    )

    for video in response["items"]:
        yield {
            "name": video["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={video['id']['videoId']}",
        }
