# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Load Balancer listeners."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_load_balancer_listener
short_description: Manage listeners in an OCI load balancer
description:
    - Create, update, and delete listeners within an existing Oracle Cloud
      Infrastructure load balancer.
    - Listeners are identified by name (not OCID) and operations are
      asynchronous via work requests.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    load_balancer_id:
        description:
            - The OCID of the load balancer that contains the listener.
        type: str
        required: true
    name:
        description:
            - The name of the listener.
            - Must be unique within the load balancer.
        type: str
        required: true
    default_backend_set_name:
        description:
            - The name of the backend set to which the listener routes traffic.
            - Required when creating a listener.
        type: str
    port:
        description:
            - The communication port for the listener.
            - Required when creating a listener.
        type: int
    protocol:
        description:
            - The protocol on which the listener accepts connection requests.
        type: str
        choices: [HTTP, TCP]
        default: HTTP
    ssl_configuration:
        description:
            - The SSL configuration for the listener.
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
    connection_configuration:
        description:
            - Configuration details for the connection between the client and
              the backend servers.
        type: dict
        suboptions:
            idle_timeout:
                description: >-
                    The maximum idle time in seconds before the connection is
                    closed. Default is 60 seconds.
                type: int
                default: 60
            backend_tcp_proxy_protocol_version:
                description: >-
                    The backend TCP proxy protocol version (1 or 2). Set to 0
                    to disable.
                type: int
    routing_policies:
        description:
            - A list of routing policy names attached to the listener.
        type: list
        elements: str
    rule_set_names:
        description:
            - A list of rule set names attached to the listener.
        type: list
        elements: str
    state:
        description:
            - The desired state of the listener.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create an HTTP listener
  stevefulme1.oci_cloud.oci_load_balancer_listener:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    name: "http-listener"
    default_backend_set_name: "my-backend-set"
    port: 80
    protocol: "HTTP"
    state: present

- name: Create an HTTPS listener with SSL
  stevefulme1.oci_cloud.oci_load_balancer_listener:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    name: "https-listener"
    default_backend_set_name: "my-backend-set"
    port: 443
    protocol: "HTTP"
    ssl_configuration:
      certificate_name: "my-cert"
      verify_peer_certificate: false
    state: present

- name: Update listener to use a different backend set
  stevefulme1.oci_cloud.oci_load_balancer_listener:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    name: "http-listener"
    default_backend_set_name: "new-backend-set"
    port: 80
    protocol: "HTTP"
    state: present

- name: Delete a listener
  stevefulme1.oci_cloud.oci_load_balancer_listener:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    name: "http-listener"
    state: absent
"""

RETURN = r"""
resource:
    description: The listener resource.
    returned: on success
    type: dict
    sample:
        name: "http-listener"
        default_backend_set_name: "my-backend-set"
        port: 80
        protocol: "HTTP"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
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
        ConnectionConfigurationDetails,
        CreateListenerDetails,
        SSLConfigurationDetails,
        UpdateListenerDetails,
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


def build_ssl_configuration(ssl_params):
    """Build SSLConfigurationDetails from module params."""
    if ssl_params is None:
        return None
    return SSLConfigurationDetails(
        certificate_name=ssl_params["certificate_name"],
        verify_depth=ssl_params.get("verify_depth", 5),
        verify_peer_certificate=ssl_params.get("verify_peer_certificate", True),
    )


def build_connection_configuration(conn_params):
    """Build ConnectionConfigurationDetails from module params."""
    if conn_params is None:
        return None
    kwargs = {
        "idle_timeout": conn_params.get("idle_timeout", 60),
    }
    if conn_params.get("backend_tcp_proxy_protocol_version") is not None:
        kwargs["backend_tcp_proxy_protocol_version"] = conn_params[
            "backend_tcp_proxy_protocol_version"
        ]
    return ConnectionConfigurationDetails(**kwargs)


def get_listener(client, load_balancer_id, name):
    """Retrieve a listener by name from the load balancer, or None if not found."""
    try:
        lb = client.get_load_balancer(load_balancer_id).data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise
    listeners = lb.listeners or {}
    return listeners.get(name)


def create_listener(module, client):
    """Create a new listener."""
    params = module.params
    details = CreateListenerDetails(
        name=params["name"],
        default_backend_set_name=params["default_backend_set_name"],
        port=params["port"],
        protocol=params.get("protocol", "HTTP"),
        ssl_configuration=build_ssl_configuration(params.get("ssl_configuration")),
        connection_configuration=build_connection_configuration(
            params.get("connection_configuration")
        ),
        routing_policy_names=params.get("routing_policies"),
        rule_set_names=params.get("rule_set_names"),
    )
    response = client.create_listener(params["load_balancer_id"], details)
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)
    return get_listener(client, params["load_balancer_id"], params["name"])


def update_listener(module, client):
    """Update an existing listener."""
    params = module.params
    details = UpdateListenerDetails(
        default_backend_set_name=params["default_backend_set_name"],
        port=params["port"],
        protocol=params.get("protocol", "HTTP"),
        ssl_configuration=build_ssl_configuration(params.get("ssl_configuration")),
        connection_configuration=build_connection_configuration(
            params.get("connection_configuration")
        ),
        routing_policy_names=params.get("routing_policies"),
        rule_set_names=params.get("rule_set_names"),
    )
    response = client.update_listener(
        params["load_balancer_id"], params["name"], details
    )
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)
    return get_listener(client, params["load_balancer_id"], params["name"])


def delete_listener(module, client):
    """Delete a listener."""
    params = module.params
    response = client.delete_listener(params["load_balancer_id"], params["name"])
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)


def needs_update(current, module):
    """Check if the listener needs updating."""
    params = module.params

    if params.get("default_backend_set_name") and \
       current.default_backend_set_name != params["default_backend_set_name"]:
        return True

    if params.get("port") is not None and current.port != params["port"]:
        return True

    if params.get("protocol") and current.protocol != params["protocol"]:
        return True

    if params.get("rule_set_names") is not None:
        current_rules = sorted(current.rule_set_names or [])
        desired_rules = sorted(params["rule_set_names"])
        if current_rules != desired_rules:
            return True

    if params.get("routing_policies") is not None:
        current_routing = sorted(current.routing_policy_names or [])
        desired_routing = sorted(params["routing_policies"])
        if current_routing != desired_routing:
            return True

    return False


def main():
    module_args = dict(
        load_balancer_id=dict(type="str", required=True),
        name=dict(type="str", required=True),
        default_backend_set_name=dict(type="str"),
        port=dict(type="int"),
        protocol=dict(type="str", default="HTTP", choices=["HTTP", "TCP"]),
        ssl_configuration=dict(
            type="dict",
            options=dict(
                certificate_name=dict(type="str", required=True),
                verify_depth=dict(type="int", default=5),
                verify_peer_certificate=dict(type="bool", default=True),
            ),
        ),
        connection_configuration=dict(
            type="dict",
            options=dict(
                idle_timeout=dict(type="int", default=60),
                backend_tcp_proxy_protocol_version=dict(type="int"),
            ),
        ),
        routing_policies=dict(type="list", elements="str"),
        rule_set_names=dict(type="list", elements="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("default_backend_set_name", "port"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, LoadBalancerClient)
    state = module.params["state"]
    current = get_listener(
        client, module.params["load_balancer_id"], module.params["name"]
    )

    if state == "absent":
        if current is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_listener(module, client)
        module.exit_json(changed=True)
        return

    # state == present
    if current is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_listener(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    if needs_update(current, module):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_listener(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(current))


if __name__ == "__main__":
    main()
