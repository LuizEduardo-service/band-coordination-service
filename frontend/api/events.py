from api.client import APIClient


async def list_events(
    client: APIClient,
    slug: str,
    upcoming: bool | None = None,
    ordering: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list:
    query_params: list[str] = []
    if upcoming is not None:
        query_params.append(f"upcoming={'true' if upcoming else 'false'}")
    if ordering:
        query_params.append(f'ordering={ordering}')
    if date_from:
        query_params.append(f'date_from={date_from}')
    if date_to:
        query_params.append(f'date_to={date_to}')

    query = ''
    if query_params:
        query = '?' + '&'.join(query_params)

    return await client.get(f'/groups/{slug}/events/{query}')


async def get_events(client: APIClient, slug: str) -> list:
    return await list_events(client, slug)


async def create_event(client: APIClient, slug: str, data: dict) -> dict:
    return await client.post(f'/groups/{slug}/events/', data)


async def get_event(client: APIClient, slug: str, event_id: int) -> dict:
    return await client.get(f'/groups/{slug}/events/{event_id}/')


async def update_event(client: APIClient, slug: str, event_id: int, data: dict) -> dict:
    return await client.patch(f'/groups/{slug}/events/{event_id}/', data)


async def delete_event(client: APIClient, slug: str, event_id: int) -> None:
    return await client.delete(f'/groups/{slug}/events/{event_id}/')


async def list_event_members(client: APIClient, slug: str, event_id: int) -> list:
    return await client.get(f'/groups/{slug}/events/{event_id}/members/')


async def add_event_member(
    client: APIClient,
    slug: str,
    event_id: int,
    membership_id: int,
    *,
    instruments: list[str],
    role_in_event: str = '',
) -> dict:
    payload: dict = {'membership_id': membership_id, 'instruments': instruments}
    if role_in_event:
        payload['role_in_event'] = role_in_event
    return await client.post(f'/groups/{slug}/events/{event_id}/members/', payload)


async def update_event_member(client: APIClient, slug: str, event_id: int, member_id: int, data: dict) -> dict:
    return await client.patch(f'/groups/{slug}/events/{event_id}/members/{member_id}/', data)


async def remove_event_member(client: APIClient, slug: str, event_id: int, member_id: int) -> None:
    return await client.delete(f'/groups/{slug}/events/{event_id}/members/{member_id}/')


async def update_participation(
    client: APIClient,
    slug: str,
    event_id: int,
    member_id: int,
    participation: str,
) -> dict:
    return await client.patch(
        f'/groups/{slug}/events/{event_id}/members/{member_id}/participation/',
        {'participation': participation},
    )


async def list_event_songs(client: APIClient, slug: str, event_id: int) -> list:
    return await client.get(f'/groups/{slug}/events/{event_id}/songs/')


async def add_event_song(client: APIClient, slug: str, event_id: int, song_id: int, order: int = 0) -> dict:
    return await client.post(
        f'/groups/{slug}/events/{event_id}/songs/',
        {'song_id': song_id, 'order': order},
    )


async def update_event_song(client: APIClient, slug: str, event_id: int, event_song_id: int, data: dict) -> dict:
    return await client.patch(f'/groups/{slug}/events/{event_id}/songs/{event_song_id}/', data)


async def remove_event_song(client: APIClient, slug: str, event_id: int, event_song_id: int) -> None:
    return await client.delete(f'/groups/{slug}/events/{event_id}/songs/{event_song_id}/')
