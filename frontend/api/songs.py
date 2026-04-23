from api.client import APIClient


async def get_songs(client: APIClient, slug: str) -> list:
    return await client.get(f'/groups/{slug}/songs/')


async def add_song(client: APIClient, slug: str, title: str, artist: str, key: str, notes: str = '', link: str = '') -> dict:
    return await client.post(f'/groups/{slug}/songs/', {
        'title': title,
        'artist': artist,
        'key': key,
        'notes': notes,
        'link': link
    })


async def delete_song(client: APIClient, slug: str, pk: int) -> None:
    return await client.delete(f'/groups/{slug}/songs/{pk}/')
