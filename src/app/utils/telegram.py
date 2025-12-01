from httpx import AsyncClient

from config import config


async def send_photo_to_telegram(file_bytes, filename, content_type) -> str:

    async with AsyncClient() as client:
        resp = await client.post(
            config.send_photo_link,
            data={'chat_id': config.service.service_chat_id},
            files={
                'photo': (
                    filename,
                    file_bytes,
                    content_type,
                )
            },
        )

    resp.raise_for_status()
    result_json = resp.json()

    file_id = result_json['result']['photo'][-1]['file_id']
    return file_id
