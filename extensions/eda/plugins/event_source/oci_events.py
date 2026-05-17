"""Poll Oci_Cloud for events."""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None


def _validate_host(host: str) -> bool:
    """Validate host parameter to prevent SSRF and ensure OCI patterns."""
    import re
    import urllib.parse

    # Block scheme injection
    if "://" in host:
        logger.error(
            "Host parameter must not include a URL scheme (got '%s'). "
            "Provide only the hostname, e.g. 'events.us-ashburn-1.oci.oraclecloud.com'.",
            host,
        )
        return False

    # Block path traversal and query injection
    if re.search(r'[/?#@]', host):
        logger.error("Host parameter contains invalid characters: %s", host)
        return False

    # Warn if host doesn't look like an OCI endpoint
    oci_pattern = re.compile(
        r'^[a-z0-9._-]+\.oci\.oraclecloud\.com$', re.IGNORECASE
    )
    if not oci_pattern.match(host):
        logger.warning(
            "Host '%s' does not match expected OCI pattern "
            "(*.oci.oraclecloud.com). Proceeding, but verify this is correct.",
            host,
        )

    return True


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    host = args["host"]

    if not _validate_host(host):
        logger.error("Host validation failed — event source will not start.")
        return

    interval = int(args.get("interval", 60))
    api_key = args.get("api_key", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    seen = set()
    while True:
        try:
            resp = requests.get(
                f"https://{host}/api/v1/events",
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            for item in resp.json().get("data", []):
                item_id = str(item.get("id", ""))
                if item_id and item_id not in seen:
                    seen.add(item_id)
                    await queue.put(dict([("oci_cloud", item)]))
        except Exception as exc:
            logger.error("Error polling: %s", exc)
        await asyncio.sleep(interval)
