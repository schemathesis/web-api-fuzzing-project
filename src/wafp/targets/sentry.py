from typing import Any, Dict, List

import requests


def list_events(url: str, token: str, organization: str, project: str, run_id: str) -> List[Dict[str, Any]]:
    response = requests.get(
        f"{url}api/0/projects/{organization}/{project}/events/?full=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    data = response.json()
    return [event for event in data if has_tag(event, "wafp.run-id", run_id)]


def has_tag(event: Dict[str, Any], key: str, value: str) -> bool:
    for tag in event["tags"]:
        if tag["key"] == key and tag["value"] == value:
            return True
    return False
