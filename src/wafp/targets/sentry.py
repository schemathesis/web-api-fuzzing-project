from typing import Any, Dict, List

import requests


def list_events(url: str, token: str, organization: str, project: str, run_id: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    headers = {"Authorization": f"Bearer {token}"}
    next_link = make_call(f"{url}api/0/projects/{organization}/{project}/events/?full=true", headers, events, run_id)
    while next_link["results"] == "true":
        next_link = make_call(next_link["url"], headers, events, run_id)
    return events


def make_call(url: str, headers: Dict[str, str], events: List[Dict[str, Any]], run_id: str) -> Dict[str, Any]:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    events.extend((event for event in data if has_tag(event, "wafp.run-id", run_id)))
    return response.links["next"]


def has_tag(event: Dict[str, Any], key: str, value: str) -> bool:
    for tag in event["tags"]:
        if tag["key"] == key and tag["value"] == value:
            return True
    return False
