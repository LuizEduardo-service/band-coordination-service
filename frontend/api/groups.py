from api.client import APIClient


async def list_groups(client: APIClient) -> list:
    return await client.get('/groups/')


async def create_group(client: APIClient, name: str, description: str = '', slug: str = '') -> dict:
    """Cria um novo grupo."""
    payload = {'name': name}
    if description:
        payload['description'] = description
    if slug:
        payload['slug'] = slug
    return await client.post('/groups/', payload)


async def get_group(client: APIClient, slug: str) -> dict:
    """Busca detalhes de um grupo."""
    return await client.get(f'/groups/{slug}/')


async def update_group(client: APIClient, slug: str, data: dict) -> dict:
    """Atualiza dados de um grupo."""
    return await client.patch(f'/groups/{slug}/', data)


async def get_members(client: APIClient, slug: str) -> list:
    return await client.get(f'/groups/{slug}/members/')


async def add_member(client: APIClient, slug: str, user_id: int, role: str) -> dict:
    return await client.post(
        f'/groups/{slug}/members/',
        {'user_id': user_id, 'role': role, 'is_vocalist': False},
    )


async def remove_member(client: APIClient, slug: str, pk: int) -> None:
    return await client.delete(f'/groups/{slug}/members/{pk}/')


async def delete_group(client: APIClient, slug: str) -> None:
    await client.delete(f'/groups/{slug}/')


async def upload_group_avatar(client: APIClient, slug: str, file_bytes: bytes, filename: str = 'avatar.jpg') -> dict:
    mime = 'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
    return await client.post_multipart(
        f'/groups/{slug}/avatar/',
        files={'avatar': (filename, file_bytes, mime)},
    )
