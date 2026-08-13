"""Defines health check and APIClient class for observability"""
import requests, logging

# separate func for health check
def health_check(base_url: str):
    # add defined path
    url = f"{base_url.rstrip('/')}/api/v1/health"
    response = requests.get(url=url, timeout=10)
    response.raise_for_status()
    return response.json()

class ApiClient:
    # to initialize api client
    def __init__(self, base_url: str, key: str):
        self.base_url = base_url.rstrip("/")
        self.key = key
        self.session = requests.Session()
        self.logger = logging.getLogger("session.client")

    # to request and log request/response
    def request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.key}" 

        # log req and headers - remove api key from req header log by safe_headers
        self.logger.debug("REQUEST: %s %s", method, url)
        self.logger.debug("REQUEST HEADERS: %s", self.safe_headers(headers=headers))

        # send request
        response = self.session.request(method, url, headers=headers, **kwargs)

        # log response
        self.logger.debug("RESPONSE STATUS: %s", response.status_code)
        self.logger.debug("RESPONSE HEADERS: %s", dict(response.headers))
        self.logger.debug("RESPONSE BODY: %s", self.truncate_body(response.text))

        # log rate limit info
        self.logger.debug("RATE LIMIT POLICY: %s", response.headers.get("RateLimit-Policy"))
        self.logger.debug(
            "RATE LIMIT: %s remaining / %s",
            response.headers.get("RateLimit-Remaining"),
            response.headers.get("RateLimit-Limit")
        )
        self.logger.debug("RATE LIMIT RESET: %s", response.headers.get("RateLimit-Reset"))

        # log retry after if 429
        if response.status_code == 429:
            self.logger.debug("RETRY AFTER: %s", response.headers.get("Retry-After"))
        return response

    # to remove api key on auth header
    def safe_headers(self, headers):
        safe_headers = dict(headers)

        if "Authorization" in safe_headers:
            safe_headers["Authorization"] = "<REDACTED>"
        return safe_headers

    # to truncate if large body
    def truncate_body(self, body):
        result = body
        length = len(body)

        if length > 10_000:
            result = (
                body[:10_000] + f" ... [truncated from {length} total characters]"
            )
        return result