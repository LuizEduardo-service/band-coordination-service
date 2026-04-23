from api.client import APIClient


async def list_invites(client: APIClient, *, status: str | None = None) -> list:
    path = '/invites/'
    if status:
        path = f'/invites/?status={status}'
    return await client.get(path)


async def pending_invite_count(client: APIClient) -> int:
    data = await client.get('/invites/pending-count/')
    return int(data.get('count', 0))


async def accept_invite(client: APIClient, invite_id: int) -> dict:
    return await client.post(f'/invites/{invite_id}/accept/', {})


async def decline_invite(client: APIClient, invite_id: int) -> dict:
    return await client.post(f'/invites/{invite_id}/decline/', {})


async def create_group_invite(client: APIClient, slug: str, invitee_id: int, role: str = 'member') -> dict:
    return await client.post(f'/groups/{slug}/invites/', {'invitee_id': invitee_id, 'role': role})


async def create_event_invite(
    client: APIClient,
    slug: str,
    event_id: int,
    invitee_id: int,
    instruments: list[str],
    role_in_event: str = '',
) -> dict:
    return await client.post(
        f'/groups/{slug}/events/{event_id}/invites/',
        {
            'invitee_id': invitee_id,
            'instruments': instruments,
            'role_in_event': role_in_event,
        },
    )
