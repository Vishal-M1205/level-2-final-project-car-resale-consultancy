import asyncio
import random

import httpx

from app.core.config import config
from app.exceptions.email_exception import EmailException


class EmailService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def send_mail(self, payload: dict):
        for attempt in range(config.max_retries):
            try:
                response = await self.client.post(
                    "https://api.mailjet.com/v3.1/send", json=payload
                )
                if response.status_code == 200:
                    break
                elif response.status_code in [429, 500, 501, 502]:
                    if attempt == config.max_retries - 1:
                        response.raise_for_status()
                    retry_after = response.headers.get("retry_after", None)
                    try:
                        if retry_after:
                            delay = float(retry_after)
                        else:
                            raise ValueError
                    except (ValueError, TypeError):
                        delay = min(config.base_delay * (2**attempt), config.max_delay)
                        delay += random.uniform(0, 1)
                    await asyncio.sleep(delay)
                    continue
                response.raise_for_status()
            except httpx.TimeoutException as error:
                raise EmailException(
                    f"Timeout Error in MailJet Email Service : {error}"
                )

            except httpx.HTTPStatusError as error:
                raise EmailException(
                    f"Timeout Error in MailJet Email Service : Status Code - {error.response.status_code} : Text {error.response.text}"
                )
