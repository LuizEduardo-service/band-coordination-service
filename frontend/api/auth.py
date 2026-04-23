from api.client import APIClient


async def login(client: APIClient, username: str, password: str) -> dict:
    return await client.post('/auth/login/', {'username': username, 'password': password})


async def register_account(client: APIClient, payload: dict) -> dict:
    return await client.post('/auth/register/', payload)


async def get_me(client: APIClient) -> dict:
    return await client.get('/auth/me/')


async def patch_me(client: APIClient, payload: dict) -> dict:
    return await client.patch('/auth/me/', payload)


async def upload_me_photo(client: APIClient, file_bytes: bytes, filename: str) -> dict:
    return await client.post_multipart(
        '/auth/me/photo/',
        files={'photo': (filename, file_bytes)},
    )
