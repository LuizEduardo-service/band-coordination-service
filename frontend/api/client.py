import httpx
import flet as ft
from state.app_state import AppState


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f'[{status_code}] {detail}')


class APIClient:
    BASE_URL = 'http://localhost:8000/api/v1'

    def __init__(self, state: AppState, page: ft.Page):
        self._state = state
        self._page = page

    def _headers(self) -> dict:
        headers = {'Content-Type': 'application/json'}
        if self._state.token:
            headers['Authorization'] = f'Bearer {self._state.token}'
        return headers

    async def _refresh(self) -> bool:
        if not self._state.refresh_token:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f'{self.BASE_URL}/auth/refresh/',
                    json={'refresh': self._state.refresh_token},
                )
            if resp.status_code == 200:
                data = resp.json()
                self._state.token = data['access']
                self._state.refresh_token = data.get('refresh', self._state.refresh_token)
                self._state.save(self._page)
                return True
        except Exception:
            pass
        return False

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f'{self.BASE_URL}{path}',
                headers=self._headers(),
                **kwargs,
            )
        if resp.status_code == 401:
            refreshed = await self._refresh()
            if refreshed:
                async with httpx.AsyncClient() as client:
                    resp = await client.request(
                        method,
                        f'{self.BASE_URL}{path}',
                        headers=self._headers(),
                        **kwargs,
                    )
            if resp.status_code == 401:
                self._state.clear(self._page)
                self._page.go('/login')
                raise APIError(401, 'Sessão expirada.')
        if not resp.is_success:
            try:
                detail = resp.json().get('detail', resp.text)
            except Exception:
                detail = resp.text
            raise APIError(resp.status_code, detail)
        return resp

    async def get(self, path: str) -> dict | list:
        resp = await self._request('GET', path)
        return resp.json()

    async def post(self, path: str, data: dict) -> dict:
        resp = await self._request('POST', path, json=data)
        return resp.json()

    async def patch(self, path: str, data: dict) -> dict:
        resp = await self._request('PATCH', path, json=data)
        return resp.json()

    async def post_multipart(self, path: str, files: dict, data: dict | None = None) -> dict:
        headers: dict = {}
        if self._state.token:
            headers['Authorization'] = f'Bearer {self._state.token}'

        async def do_post():
            async with httpx.AsyncClient() as client:
                return await client.post(
                    f'{self.BASE_URL}{path}',
                    headers=headers,
                    files=files,
                    data=data or {},
                )

        resp = await do_post()
        if resp.status_code == 401:
            refreshed = await self._refresh()
            if refreshed:
                headers['Authorization'] = f'Bearer {self._state.token}'
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f'{self.BASE_URL}{path}',
                        headers=headers,
                        files=files,
                        data=data or {},
                    )
            if resp.status_code == 401:
                self._state.clear(self._page)
                self._page.go('/login')
                raise APIError(401, 'Sessão expirada.')
        if not resp.is_success:
            try:
                body = resp.json()
                detail = body.get('detail', body)
                if isinstance(detail, dict):
                    detail = str(detail)
            except Exception:
                detail = resp.text
            raise APIError(resp.status_code, str(detail))
        return resp.json()

    async def delete(self, path: str) -> None:
        await self._request('DELETE', path)
