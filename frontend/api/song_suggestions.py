from api.client import APIClient


async def create_song_suggestion(
    client: APIClient,
    slug: str,
    *,
    title: str,
    artist: str = '',
    key: str = '',
    notes: str = '',
    link: str = '',
) -> dict:
    payload: dict = {'title': title}
    if artist:
        payload['artist'] = artist
    if key:
        payload['key'] = key
    if notes:
        payload['notes'] = notes
    if link:
        payload['link'] = link
    return await client.post(f'/groups/{slug}/song-suggestions/', payload)


async def list_pending_song_suggestions(client: APIClient) -> list:
    return await client.get('/song-suggestions/pending/')


async def pending_song_suggestion_count(client: APIClient) -> int:
    data = await client.get('/song-suggestions/pending-count/')
    return int(data.get('count', 0))


async def approve_song_suggestion(client: APIClient, suggestion_id: int) -> dict:
    return await client.post(f'/song-suggestions/{suggestion_id}/approve/', {})


async def reject_song_suggestion(client: APIClient, suggestion_id: int) -> dict:
    return await client.post(f'/song-suggestions/{suggestion_id}/reject/', {})
