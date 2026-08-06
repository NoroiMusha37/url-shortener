import httpx

from app.logger import LoggerMixin


class IPAPIClient(LoggerMixin):
    batch_endpoint = "http://ip-api.com/batch"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_ips_data(self, ips: list) -> dict:
        self.log_info("Executing POST request to ip-api batch...")
        params = {
            "fields": "status,message,country,regionName,city,query"
        }

        try:
            result = await self.client.post(
                self.batch_endpoint, params=params, json=ips
            )
            result.raise_for_status()

            return result.json()
        except httpx.HTTPStatusError as e:
            self.log_error(f"API rejected request", error=e)
            raise
        except httpx.RequestError as e:
            self.log_error("Network connection failed", error=e)
            raise
        except ValueError as e:
            self.log_error("Failed to decode JSON from response", error=e)
            raise
