#!/usr/bin/env python3
"""Emit Veracode findings as newline-delimited JSON for a Splunk scripted input."""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional
from urllib.parse import urlparse


APP_ROOT = Path(__file__).resolve().parents[1]
VENDORED_LIB = APP_ROOT / "lib"
if VENDORED_LIB.is_dir():
    sys.path.insert(0, str(VENDORED_LIB))

import requests  # noqa: E402
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC  # noqa: E402


APPLICATIONS_URL = "https://api.veracode.com/appsec/v1/applications"
FINDINGS_URL = "https://api.veracode.com/appsec/v2/applications/{guid}/findings?size=500"
API_HOST = "api.veracode.com"
MAX_ATTEMPTS = 5
REQUEST_TIMEOUT = (10, 60)
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
LOGGER = logging.getLogger("ta_veracode")


def _retry_delay(response: Optional[requests.Response], attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After", "").strip()
        if retry_after.isdigit():
            return min(float(retry_after), 120.0)
    return min(float(2 ** (attempt - 1)), 30.0)


def _validated_api_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != API_HOST:
        raise ValueError(f"Refusing unexpected pagination URL: {url}")
    return url


def request_json(
    session: requests.Session,
    url: str,
    auth: RequestsAuthPluginVeracodeHMAC,
) -> Mapping[str, Any]:
    """Request one Veracode API page with bounded retries."""

    validated_url = _validated_api_url(url)
    last_error: Optional[BaseException] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response: Optional[requests.Response] = None
        try:
            response = session.get(
                validated_url,
                auth=auth,
                headers={"Accept": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code not in RETRYABLE_STATUS:
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, Mapping):
                    raise ValueError("Veracode returned a non-object JSON response")
                return payload
            last_error = requests.HTTPError(
                f"Veracode returned retryable HTTP {response.status_code}", response=response
            )
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if response is not None and response.status_code not in RETRYABLE_STATUS:
                raise

        if attempt == MAX_ATTEMPTS:
            break
        delay = _retry_delay(response, attempt)
        LOGGER.warning(
            "Veracode request attempt %d/%d failed; retrying in %.0f seconds",
            attempt,
            MAX_ATTEMPTS,
            delay,
        )
        time.sleep(delay)

    raise RuntimeError(f"Veracode request failed after {MAX_ATTEMPTS} attempts") from last_error


def paginated_items(
    session: requests.Session,
    auth: RequestsAuthPluginVeracodeHMAC,
    start_url: str,
    collection_name: str,
) -> Iterable[Mapping[str, Any]]:
    """Yield objects from a HAL-style Veracode paginated collection."""

    url: Optional[str] = start_url
    while url:
        payload = request_json(session, url, auth)
        embedded = payload.get("_embedded", {})
        if not isinstance(embedded, Mapping):
            raise ValueError("Veracode response has an invalid _embedded object")
        items = embedded.get(collection_name, [])
        if not isinstance(items, list):
            raise ValueError(f"Veracode response has an invalid {collection_name} collection")
        for item in items:
            if isinstance(item, Mapping):
                yield item

        links = payload.get("_links", {})
        next_link = links.get("next", {}) if isinstance(links, Mapping) else {}
        next_url = next_link.get("href") if isinstance(next_link, Mapping) else None
        url = _validated_api_url(str(next_url)) if next_url else None


def get_applications(
    session: requests.Session, auth: RequestsAuthPluginVeracodeHMAC
) -> List[Mapping[str, Any]]:
    return list(paginated_items(session, auth, APPLICATIONS_URL, "applications"))


def get_findings(
    session: requests.Session, auth: RequestsAuthPluginVeracodeHMAC, application_guid: str
) -> List[Mapping[str, Any]]:
    url = FINDINGS_URL.format(guid=application_guid)
    return list(paginated_items(session, auth, url, "findings"))


def application_name(application: Mapping[str, Any]) -> str:
    profile = application.get("profile", {})
    if isinstance(profile, Mapping) and profile.get("name"):
        return str(profile["name"])
    return "Unknown application"


def finding_event(
    application: Mapping[str, Any], finding: Mapping[str, Any]
) -> Dict[str, Any]:
    return {
        "veracode_application": {
            "guid": str(application.get("guid", "")),
            "name": application_name(application),
        },
        "veracode_finding": dict(finding),
    }


def collect_events(
    session: requests.Session, auth: RequestsAuthPluginVeracodeHMAC
) -> Iterable[Dict[str, Any]]:
    applications = get_applications(session, auth)
    LOGGER.info("Found %d Veracode applications", len(applications))
    for application in applications:
        guid = str(application.get("guid", ""))
        if not guid:
            LOGGER.warning("Skipping an application without a GUID")
            continue
        findings = get_findings(session, auth, guid)
        LOGGER.info("Application %s returned %d findings", application_name(application), len(findings))
        for finding in findings:
            yield finding_event(application, finding)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    session = requests.Session()
    session.headers.update({"User-Agent": "TA-veracode/2.0"})
    auth = RequestsAuthPluginVeracodeHMAC()
    try:
        count = 0
        for event in collect_events(session, auth):
            print(json.dumps(event, separators=(",", ":"), ensure_ascii=False))
            count += 1
        LOGGER.info("Emitted %d Veracode finding events", count)
        return 0
    except Exception:
        LOGGER.exception("Veracode collection failed")
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
