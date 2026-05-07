"""Waiter and retry utilities for OCI resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module_utils: oci_wait
short_description: Waiter and retry utilities for OCI API operations
description:
  - Provides wait_for_resource to poll an OCI resource until it reaches a target
    lifecycle state, with configurable timeout and failure state detection.
  - Includes wait_for_work_request for tracking OCI async work requests, and
    call_with_retry for exponential backoff retries on transient API errors.
author:
  - Steve Fulmer (@stevefulme1)
"""

import time

try:
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def wait_for_resource(
    module,
    get_fn,
    resource_id,
    target_states,
    failure_states=None,
):
    """Poll a resource until it reaches a target lifecycle state."""
    wait = module.params.get("wait", True)
    if not wait:
        return get_fn(resource_id).data

    timeout = module.params.get("wait_timeout", 1200)
    interval = module.params.get("wait_interval", 30)

    if failure_states is None:
        failure_states = frozenset({"FAILED"})

    start = time.monotonic()
    while True:
        try:
            response = get_fn(resource_id)
            resource = response.data
        except ServiceError as e:
            if e.status == 404 and "TERMINATED" in target_states:
                return None
            if e.status == 404 and "DELETED" in target_states:
                return None
            raise

        state = getattr(resource, "lifecycle_state", None)
        if state in target_states:
            return resource
        if state in failure_states:
            module.fail_json(
                msg=f"Resource {resource_id} entered failure state: {state}",
            )

        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            module.fail_json(
                msg=f"Timed out waiting for resource {resource_id} to reach "
                f"state {target_states}. Current state: {state}",
            )
        time.sleep(min(interval, timeout - elapsed))


def wait_for_work_request(
    module,
    client,
    work_request_id,
):
    """Wait for an OCI work request to complete."""
    timeout = module.params.get("wait_timeout", 1200)
    interval = module.params.get("wait_interval", 30)

    start = time.monotonic()
    while True:
        wr = client.get_work_request(work_request_id).data
        if wr.status in ("SUCCEEDED", "COMPLETED"):
            return wr
        if wr.status in ("FAILED", "CANCELED"):
            module.fail_json(
                msg=f"Work request {work_request_id} {wr.status}",
            )

        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            module.fail_json(
                msg=f"Timed out waiting for work request {work_request_id}. "
                f"Status: {wr.status}",
            )
        time.sleep(min(interval, timeout - elapsed))


def call_with_retry(fn, *args, max_retries=3, retry_on=(429, 500, 503), **kwargs):
    """Call an OCI API function with exponential backoff retry."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except ServiceError as e:
            last_error = e
            if e.status not in retry_on or attempt == max_retries:
                raise
            time.sleep(2 ** attempt)
    raise last_error
