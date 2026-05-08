# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Load Balancer health checker configuration."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_load_balancer_health_checker
short_description: Manage health checker configuration for an OCI load balancer backend set
description:
    - Update the health checker configuration for a backend set within an
      existing Oracle Cloud Infrastructure load balancer.
    - Health checkers cannot be deleted independently; they are an intrinsic
      part of a backend set. This module only supports state=present.
    - Operations are asynchronous via work requests.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    load_balancer_id:
        description:
            - The OCID of the load balancer that contains the backend set.
        type: str
        required: true
    backend_set_name:
        description:
            - The name of the backend set whose health checker to manage.
        type: str
        required: true
    protocol:
        description:
            - The protocol used for health checks.
        type: str
        choices: [HTTP, TCP]
        default: HTTP
    port:
        description:
            - The backend server port against which to run the health check.
        type: int
        required: true
    url_path:
        description:
            - The path against which to run the health check (HTTP only).
        type: str
        default: /
    interval_in_millis:
        description:
            - The interval between health checks in milliseconds.
        type: int
        default: 10000
    timeout_in_millis:
        description:
            - The maximum time in milliseconds to wait for a reply to a health
              check. A health check is successful only if a reply returns
              within this timeout period.
        type: int
        default: 3000
    retries:
        description:
            - The number of retries to attempt before a backend server is
              considered unhealthy.
        type: int
        default: 3
    return_code:
        description:
            - The expected HTTP status code for a healthy response.
        type: int
        default: 200
    response_body_regex:
        description:
            - A regular expression for parsing the response body from the
              backend server. If the regex matches, the health check is
              considered successful.
        type: str
        default: ""
    state:
        description:
            - The desired state. Only C(present) is supported because health
              checkers cannot be deleted independently of their backend set.
        type: str
        default: present
        choices: [present]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Update health checker to use HTTP on port 8080
  stevefulme1.oci_cloud.oci_load_balancer_health_checker:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    backend_set_name: "my-backend-set"
    protocol: "HTTP"
    port: 8080
    url_path: "/health"
    interval_in_millis: 10000
    timeout_in_millis: 3000
    retries: 3
    return_code: 200
    state: present

- name: Configure TCP health check
  stevefulme1.oci_cloud.oci_load_balancer_health_checker:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    backend_set_name: "my-backend-set"
    protocol: "TCP"
    port: 3306
    interval_in_millis: 30000
    timeout_in_millis: 5000
    retries: 5
    state: present

- name: Increase health check frequency
  stevefulme1.oci_cloud.oci_load_balancer_health_checker:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    backend_set_name: "my-backend-set"
    protocol: "HTTP"
    port: 80
    url_path: "/status"
    interval_in_millis: 5000
    timeout_in_millis: 2000
    retries: 2
    response_body_regex: ".*OK.*"
    state: present
"""

RETURN = r"""
resource:
    description: The health checker configuration.
    returned: on success
    type: dict
    sample:
        protocol: "HTTP"
        port: 8080
        url_path: "/health"
        interval_in_millis: 10000
        timeout_in_millis: 3000
        retries: 3
        return_code: 200
        response_body_regex: ""
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import (
    create_service_client,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    wait_for_work_request,
)

try:
    from oci.load_balancer import LoadBalancerClient
    from oci.load_balancer.models import (
        HealthCheckerDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_health_checker(client, load_balancer_id, backend_set_name):
    """Retrieve the health checker for a backend set, or None if not found."""
    try:
        return client.get_health_checker(load_balancer_id, backend_set_name).data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def update_health_checker(module, client):
    """Update the health checker configuration."""
    params = module.params
    details = HealthCheckerDetails(
        protocol=params.get("protocol", "HTTP"),
        port=params["port"],
        url_path=params.get("url_path", "/"),
        interval_in_millis=params.get("interval_in_millis", 10000),
        timeout_in_millis=params.get("timeout_in_millis", 3000),
        retries=params.get("retries", 3),
        return_code=params.get("return_code", 200),
        response_body_regex=params.get("response_body_regex", ""),
    )
    response = client.update_health_checker(
        params["load_balancer_id"], params["backend_set_name"], details
    )
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)
    return get_health_checker(
        client, params["load_balancer_id"], params["backend_set_name"]
    )


def needs_update(current, module):
    """Check if the health checker needs updating."""
    params = module.params
    checks = [
        ("protocol", current.protocol, params.get("protocol", "HTTP")),
        ("port", current.port, params["port"]),
        ("url_path", current.url_path, params.get("url_path", "/")),
        ("interval_in_millis", current.interval_in_millis, params.get("interval_in_millis", 10000)),
        ("timeout_in_millis", current.timeout_in_millis, params.get("timeout_in_millis", 3000)),
        ("retries", current.retries, params.get("retries", 3)),
        ("return_code", current.return_code, params.get("return_code", 200)),
        ("response_body_regex", current.response_body_regex, params.get("response_body_regex", "")),
    ]
    for _attr, current_val, desired_val in checks:
        if current_val != desired_val:
            return True
    return False


def main():
    module_args = dict(
        load_balancer_id=dict(type="str", required=True),
        backend_set_name=dict(type="str", required=True),
        protocol=dict(type="str", default="HTTP", choices=["HTTP", "TCP"]),
        port=dict(type="int", required=True),
        url_path=dict(type="str", default="/"),
        interval_in_millis=dict(type="int", default=10000),
        timeout_in_millis=dict(type="int", default=3000),
        retries=dict(type="int", default=3),
        return_code=dict(type="int", default=200),
        response_body_regex=dict(type="str", default=""),
        state=dict(type="str", default="present", choices=["present"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, LoadBalancerClient)
    current = get_health_checker(
        client, module.params["load_balancer_id"], module.params["backend_set_name"]
    )

    if current is None:
        module.fail_json(
            msg=f"Backend set '{module.params['backend_set_name']}' not found "
            f"in load balancer '{module.params['load_balancer_id']}'. "
            f"A health checker can only be updated on an existing backend set."
        )

    if needs_update(current, module):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_health_checker(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(current))


if __name__ == "__main__":
    main()
