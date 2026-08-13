"""Orchestration for api discovery"""
from utils.log_config import setup_logging
from utils.client import health_check, ApiClient
from utils.submit import submit_answer
from dotenv import load_dotenv, find_dotenv
import os, sys, logging, json

# to check health without starting clock
def run_health(base_url: str):
    setup_logging()
    log = logging.getLogger("session.main")
    result = health_check(base_url)
    log.info("Health OK: %s", result)

# to run first authenticated request
def run_start(base_url: str, api_key: str):
    setup_logging()
    log = logging.getLogger("session.main")
    log.warning("first authenticated request — clock start")
    client = ApiClient(base_url, api_key)
    resp = client.request("GET", "/api/v1/time") # time guess
    log.info("Status %s", resp.status_code)

# to discover / fetch an endpoint
def run_call(base_url: str, api_key: str, method: str, path: str, body=None):
    setup_logging()
    client = ApiClient(base_url, api_key)
    kwargs = {}
    if body is not None:
        kwargs["json"] = body
    return client.request(method, path, **kwargs)

# to request quickly with full visibility by command-line
def main():
    load_dotenv(find_dotenv())
    base_url = os.environ["BASE_URL"]
    api_key = os.environ["API_KEY"]

    # cmd arg parsing
    cmd = sys.argv[1] if len(sys.argv) > 1 else "health"

    if cmd == "health":
        run_health(base_url=base_url)
    elif cmd == "start":
        run_start(base_url=base_url, api_key=api_key)
    elif cmd == "call":
        if len(sys.argv) < 4:
            print("usage: python src/main.py call METHOD PATH --json JSON")
            sys.exit(1)

        body = None
        # to send optional body json
        if len(sys.argv) >= 6 and sys.argv[4] == "--json":
            body = json.loads(sys.argv[5])
            
        run_call(base_url=base_url, api_key=api_key, method=sys.argv[2], path=sys.argv[3], body=body)

    elif cmd == "submit":
        if len(sys.argv) < 4:
            print("usage: python main.py submit TYPE VALUE [NOTES]")
            sys.exit(1)

        setup_logging()
        client = ApiClient(base_url, api_key)
        type_ = sys.argv[2]
        value = sys.argv[3]
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        submit_answer(client, type_, value, notes=notes)

    else:
        print("usage: python main.py [health|start|call METHOD PATH] OR python main.py [submit TYPE VALUE [NOTES]]")
        sys.exit(1)

if __name__ == "__main__":
    main()