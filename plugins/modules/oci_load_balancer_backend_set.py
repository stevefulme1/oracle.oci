# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Load Balancer backend sets."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_load_balancer_backend_set
short_description: Manage backend sets in an OCI load balancer
description:
    - Create, update, and delete backend sets within an existing Oracle Cloud
      Infrastructure load balancer.
    - Backend sets are identified by name (not OCID) and operations are
      asynchronous via work requests.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    load_balancer_id:
        description:
            - The OCID of the load balancer that contains the backend set.
        type: str
        required: true
    name:
        description:
            - The name of the backend set.
            - Must be unique within the load balancer.
        type: str
        required: true
    policy:
        description:
            - The load balancing policy for the backend set.
        type: str
        choices:
            - ROUND_ROBIN
            - IP_HASH
            - LEAST_CONNECTIONS
        default: ROUND_ROBIN
    health_checker:
        description:
            - The health checker configuration for the backend set.
        type: dict
        suboptions:
            protocol:
                description: The protocol used for health checks (HTTP or TCP).
                type: str
                required: true
            port:
                description: The backend server port for health checks.
                type: int
                required: true
            url_path:
                description: The path for HTTP health checks.
                type: str
                default: /
            interval_in_millis:
                description: The interval between health checks in milliseconds.
                type: int
                default: 10000
            timeout_in_millis:
                description: The maximum time to wait for a health check response.
                type: int
                default: 3000
            retries:
                description: >-
                    The number of retries before marking the backend as unhealthy.
                type: int
                default: 3
            return_code:
                description: The expected HTTP status code for a healthy response.
                type: int
                default: 200
            response_body_regex:
                description: A regular expression to match against the response body.
                type: str
                default: ""
    backends:
        description:
            - A list of backend server configurations.
        type: list
        elements: dict
        default: []
        suboptions:
            ip_address:
                description: The IP address of the backend server.
                type: str
                required: true
            port:
                description: The communication port for the backend server.
                type: int
                required: true
            weight:
                description: The load balancing weight of the backend server.
                type: int
                default: 1
            backup:
                description: Whether this backend is a backup server.
                type: bool
                default: false
            drain:
                description: Whether this backend is draining.
                type: bool
                default: false
            offline:
                description: Whether this backend is offline.
                type: bool
                default: false
    session_persistence_configuration:
        description:
            - The session persistence configuration for the backend set.
        type: dict
        suboptions:
            cookie_name:
                description: The name of the cookie used for session persistence.
                type: str
                required: true
            disable_fallback:
                description: Whether to disable fallback to a different backend.
                type: bool
                default: false
    ssl_configuration:
        description:
            - The SSL configuration for the backend set.
        type: dict
        suboptions:
            certificate_name:
                description: The name of the SSL certificate bundle.
                type: str
                required: true
            verify_depth:
                description: The maximum depth for certificate chain verification.
                type: int
                default: 5
            verify_peer_certificate:
                description: Whether to verify the peer certificate.
                type: bool
                default: true
    state:
        description:
            - The desired state of the backend set.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a backend set with round-robin policy
  oracle.oci.oci_load_balancer_backend_set:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    name: "my-backend-set"
    policy: "ROUND_ROBIN"
    health_checker:
      protocol: "HTTP"
      port: 80
      url_path: "/health"
      interval_in_millis: 10000
      timeout_in_millis: 3000
      retries: 3
    backends:
      - ip_address: "10.0.0.1"
        port: 80
        weight: 1
      - ip_address: "10.0.0.2"
        port: 80
        weight: 1
    state: present

- name: Update backend set policy
  oracle.oci.oci_load_balancer_backend_set:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    name: "my-backend-set"
    policy: "LEAST_CONNECTIONS"
    health_checker:
      protocol: "HTTP"
      port: 80
      url_path: "/health"
    state: present

- name: Delete a backend set
  oracle.oci.oci_load_balancer_backend_set:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    name: "my-backend-set"
    state: absent
"""

RETURN = r"""
resource:
    description: The backend set resource.
    returned: on success
    type: dict
    sample:
        name: "my-backend-set"
        policy: "ROUND_ROBIN"
        backends:
            - ip_address: "10.0.0.1"
              port: 80
              weight: 1
        health_checker:
            protocol: "HTTP"
            port: 80
            url_path: "/health"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import (
    create_service_client,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    wait_for_work_request,
)

try:
    from oci.load_balancer import LoadBalancerClient
    from oci.load_balancer.models import (
        BackendDetails,
        CreateBackendSetDetails,
        HealthCheckerDetails,
        SessionPersistenceConfigurationDetails,
        SSLConfigurationDetails,
        UpdateBackendSetDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def to_dict(obj):
    """Convert an OCI SDK object to a serializable dict."""
    if obj is None:
        return {}
    if hasattr(obj, "__dict__"):
        result = {}
        for key, value in obj.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                result[key] = [to_dict(item) if hasattr(item, "__dict__") else item for item in value]
            elif hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, dict)):
                result[key] = to_dict(value)
            else:
                result[key] = value
        return result
    return obj


def build_health_checker_details(hc_params):
    """Build a HealthCheckerDetails from module params."""
    if hc_params is None:
        return None
    return HealthCheckerDetails(
        protocol=hc_params.get("protocol", "HTTP"),
        port=hc_params.get("port", 80),
        url_path=hc_params.get("url_path", "/"),
        interval_in_millis=hc_params.get("interval_in_millis", 10000),
        timeout_in_millis=hc_params.get("timeout_in_millis", 3000),
        retries=hc_params.get("retries", 3),
        return_code=hc_params.get("return_code", 200),
        response_body_regex=hc_params.get("response_body_regex", ""),
    )


def build_backend_details_list(backends_params):
    """Build a list of BackendDetails from module params."""
    if not backends_params:
        return []
    result = []
    for b in backends_params:
        result.append(
            BackendDetails(
                ip_address=b["ip_address"],
                port=b["port"],
                weight=b.get("weight", 1),
                backup=b.get("backup", False),
                drain=b.get("drain", False),
                offline=b.get("offline", False),
            )
        )
    return result


def build_session_persistence(sp_params):
    """Build SessionPersistenceConfigurationDetails from module params."""
    if sp_params is None:
        return None
    return SessionPersistenceConfigurationDetails(
        cookie_name=sp_params["cookie_name"],
        disable_fallback=sp_params.get("disable_fallback", False),
    )


def build_ssl_configuration(ssl_params):
    """Build SSLConfigurationDetails from module params."""
    if ssl_params is None:
        return None
    return SSLConfigurationDetails(
        certificate_name=ssl_params["certificate_name"],
        verify_depth=ssl_params.get("verify_depth", 5),
        verify_peer_certificate=ssl_params.get("verify_peer_certificate", True),
    )


def get_backend_set(client, load_balancer_id, name):
    """Retrieve a backend set by name, or None if not found."""
    try:
        return client.get_backend_set(load_balancer_id, name).data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def create_backend_set(module, client):
    """Create a new backend set."""
    params = module.params
    details = CreateBackendSetDetails(
        name=params["name"],
        policy=params.get("policy", "ROUND_ROBIN"),
        health_checker=build_health_checker_details(params.get("health_checker")),
        backends=build_backend_details_list(params.get("backends")),
        session_persistence_configuration=build_session_persistence(
            params.get("session_persistence_configuration")
        ),
        ssl_configuration=build_ssl_configuration(params.get("ssl_configuration")),
    )
    response = client.create_backend_set(params["load_balancer_id"], details)
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)
    return get_backend_set(client, params["load_balancer_id"], params["name"])


def update_backend_set(module, client):
    """Update an existing backend set."""
    params = module.params
    details = UpdateBackendSetDetails(
        policy=params.get("policy", "ROUND_ROBIN"),
        health_checker=build_health_checker_details(params.get("health_checker")),
        backends=build_backend_details_list(params.get("backends")),
        session_persistence_configuration=build_session_persistence(
            params.get("session_persistence_configuration")
        ),
        ssl_configuration=build_ssl_configuration(params.get("ssl_configuration")),
    )
    response = client.update_backend_set(
        params["load_balancer_id"], params["name"], details
    )
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)
    return get_backend_set(client, params["load_balancer_id"], params["name"])


def delete_backend_set(module, client):
    """Delete a backend set."""
    params = module.params
    response = client.delete_backend_set(params["load_balancer_id"], params["name"])
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)


def needs_update(current, module):
    """Check if the backend set needs updating."""
    params = module.params

    if params.get("policy") and current.policy != params["policy"]:
        return True

    hc_params = params.get("health_checker")
    if hc_params and current.health_checker:
        hc = current.health_checker
        checks = [
            ("protocol", hc.protocol),
            ("port", hc.port),
            ("url_path", hc.url_path),
            ("interval_in_millis", hc.interval_in_millis),
            ("timeout_in_millis", hc.timeout_in_millis),
            ("retries", hc.retries),
        ]
        for param_key, current_val in checks:
            desired = hc_params.get(param_key)
            if desired is not None and desired != current_val:
                return True

    backends_params = params.get("backends")
    if backends_params is not None:
        current_backends = {
            f"{b.ip_address}:{b.port}": {
                "weight": b.weight,
                "backup": b.backup,
                "drain": b.drain,
                "offline": b.offline,
            }
            for b in (current.backends or [])
        }
        desired_backends = {
            f"{b['ip_address']}:{b['port']}": {
                "weight": b.get("weight", 1),
                "backup": b.get("backup", False),
                "drain": b.get("drain", False),
                "offline": b.get("offline", False),
            }
            for b in backends_params
        }
        if current_backends != desired_backends:
            return True

    return False


def main():
    module_args = dict(
        load_balancer_id=dict(type="str", required=True),
        name=dict(type="str", required=True),
        policy=dict(
            type="str",
            default="ROUND_ROBIN",
            choices=["ROUND_ROBIN", "IP_HASH", "LEAST_CONNECTIONS"],
        ),
        health_checker=dict(
            type="dict",
            options=dict(
                protocol=dict(type="str", required=True),
                port=dict(type="int", required=True),
                url_path=dict(type="str", default="/"),
                interval_in_millis=dict(type="int", default=10000),
                timeout_in_millis=dict(type="int", default=3000),
                retries=dict(type="int", default=3),
                return_code=dict(type="int", default=200),
                response_body_regex=dict(type="str", default=""),
            ),
        ),
        backends=dict(
            type="list",
            elements="dict",
            default=[],
            options=dict(
                ip_address=dict(type="str", required=True),
                port=dict(type="int", required=True),
                weight=dict(type="int", default=1),
                backup=dict(type="bool", default=False),
                drain=dict(type="bool", default=False),
                offline=dict(type="bool", default=False),
            ),
        ),
        session_persistence_configuration=dict(
            type="dict",
            options=dict(
                cookie_name=dict(type="str", required=True),
                disable_fallback=dict(type="bool", default=False),
            ),
        ),
        ssl_configuration=dict(
            type="dict",
            options=dict(
                certificate_name=dict(type="str", required=True),
                verify_depth=dict(type="int", default=5),
                verify_peer_certificate=dict(type="bool", default=True),
            ),
        ),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, LoadBalancerClient)
    state = module.params["state"]
    current = get_backend_set(
        client, module.params["load_balancer_id"], module.params["name"]
    )

    if state == "absent":
        if current is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_backend_set(module, client)
        module.exit_json(changed=True)
        return

    # state == present
    if current is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_backend_set(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    if needs_update(current, module):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_backend_set(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(current))


if __name__ == "__main__":
    main()
