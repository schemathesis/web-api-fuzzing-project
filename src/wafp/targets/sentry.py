from typing import Any, Dict, Generator, List

import requests


def list_events(url: str, token: str, organization: str, project: str, run_id: str) -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{url}api/0/projects/{organization}/{project}/events/?full=true", headers=headers)
    response.raise_for_status()
    events: List[Dict[str, Any]] = []
    events.extend(parse_events(response, run_id))
    _, next_link = requests.utils.parse_header_links(response.headers["Link"])  # type: ignore
    while next_link["results"] == "true":
        response = requests.get(next_link["url"], headers=headers)
        response.raise_for_status()
        events.extend(parse_events(response, run_id))
        _, next_link = requests.utils.parse_header_links(response.headers["Link"])  # type: ignore
    return events


def parse_events(response: requests.Response, run_id: str) -> Generator[Dict[str, Any], None, None]:
    data = response.json()
    return (event for event in data if has_tag(event, "wafp.run-id", run_id))


def has_tag(event: Dict[str, Any], key: str, value: str) -> bool:
    for tag in event["tags"]:
        if tag["key"] == key and tag["value"] == value:
            return True
    return False
