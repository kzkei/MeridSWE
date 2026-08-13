"""To submit answers on if submit """
from utils.client import ApiClient

def submit_answer(client: ApiClient, type_: str, value: str, notes: str = ""):

    # define basic payload structure
    payload = {"type": type_, "value": value}

    # append for sys.argv[4]
    if notes:
        payload["notes"] = notes

    # post request
    response = client.request("POST", "/api/v1/submit", json=payload)

    if response.headers.get("Content-Type", "").startswith("application/json"):
        body = response.json()
    else:
        body = {"error": response.text}

    return {"status_code": response.status_code, "body": body}
