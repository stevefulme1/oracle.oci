#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Load Balancer backends."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_load_balancer_backend
short_description: Manage individual backends in an OCI load balancer backend set
description:
    - Create, update, and delete individual backend servers within a backend set
      of an existing Oracle Cloud Infrastructure load balancer.
    - Backends are identified by "ip_address:port" within their backend set.
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
            - The name of the backend set to which the backend belongs.
        type: str
        required: true
    ip_address:
        description:
            - The IP address of the backend server.
        type: str
        required: true
    port:
        description:
            - The communication port for the backend server.
        type: int
        required: true
    weight:
        description:
            - The load balancing weight assigned to the backend server.
            - Servers with higher weight receive a proportionally larger share
              of incoming traffic.
        type: int
        default: 1
    backup:
        description:
            - Whether this backend server is a backup.
            - Backup servers receive traffic only when all non-backup servers
              are unhealthy.
        type: bool
        default: false
    drain:
        description:
            - Whether the backend server is draining.
            - A draining server accepts no new connections but continues to
              serve existing ones.
        type: bool
        default: false
    offline:
        description:
            - Whether the backend server is offline.
            - An offline server accepts no traffic.
        type: bool
        default: false
    state:
        description:
            - The desired state of the backend.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Add a backend to a backend set
  oracle.oci.oci_load_balancer_backend:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    backend_set_name: "my-backend-set"
    ip_address: "10.0.0.3"
    port: 8080
    weight: 1
    state: present

- name: Update backend weight
  oracle.oci.oci_load_balancer_backend:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    backend_set_name: "my-backend-set"
    ip_address: "10.0.0.3"
    port: 8080
    weight: 3
    state: present

- name: Drain a backend server
  oracle.oci.oci_load_balancer_backend:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    backend_set_name: "my-backend-set"
    ip_address: "10.0.0.3"
    port: 8080
    drain: true
    state: present

- name: Remove a backend from a backend set
  oracle.oci.oci_load_balancer_backend:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    backend_set_name: "my-backend-set"
    ip_address: "10.0.0.3"
    port: 8080
    state: absent
"""

RETURN = r"""
resource:
    description: The backend resource.
    returned: on success
    type: dict
    sample:
        ip_address: "10.0.0.3"
        port: 8080
        weight: 1
        backup: false
        drain: false
        offline: false
        name: "10.0.0.3:8080"
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
        CreateBackendDetails,
        UpdateBackendDetails,
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


def backend_name(module):
    """Return the backend identifier in 'ip_address:port' format."""
    return f"{module.params['ip_address']}:{module.params['port']}"


def get_backend(client, load_balancer_id, backend_set_name, name):
    """Retrieve a backend by name, or None if not found."""
    try:
        return client.get_backend(load_balancer_id, backend_set_name, name).data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def create_backend(module, client):
    """Create a new backend in the backend set."""
    params = module.params
    details = CreateBackendDetails(
        ip_address=params["ip_address"],
        port=params["port"],
        weight=params.get("weight", 1),
        backup=params.get("backup", False),
        drain=params.get("drain", False),
        offline=params.get("offline", False),
    )
    response = client.create_backend(
        params["load_balancer_id"], params["backend_set_name"], details
    )
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)
    return get_backend(
        client,
        params["load_balancer_id"],
        params["backend_set_name"],
        backend_name(module),
    )


def update_backend(module, client):
    """Update an existing backend."""
    params = module.params
    details = UpdateBackendDetails(
        weight=params.get("weight", 1),
        backup=params.get("backup", False),
        drain=params.get("drain", False),
        offline=params.get("offline", False),
    )
    response = client.update_backend(
        params["load_balancer_id"],
        params["backend_set_name"],
        backend_name(module),
        details,
    )
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)
    return get_backend(
        client,
        params["load_balancer_id"],
        params["backend_set_name"],
        backend_name(module),
    )


def delete_backend(module, client):
    """Delete a backend from the backend set."""
    params = module.params
    response = client.delete_backend(
        params["load_balancer_id"],
        params["backend_set_name"],
        backend_name(module),
    )
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)


def needs_update(current, module):
    """Check if the backend needs updating."""
    params = module.params
    checks = [
        ("weight", current.weight, params.get("weight", 1)),
        ("backup", current.backup, params.get("backup", False)),
        ("drain", current.drain, params.get("drain", False)),
        ("offline", current.offline, params.get("offline", False)),
    ]
    for _attr, current_val, desired_val in checks:
        if current_val != desired_val:
            return True
    return False


def main():
    module_args = dict(
        load_balancer_id=dict(type="str", required=True),
        backend_set_name=dict(type="str", required=True),
        ip_address=dict(type="str", required=True),
        port=dict(type="int", required=True),
        weight=dict(type="int", default=1),
        backup=dict(type="bool", default=False),
        drain=dict(type="bool", default=False),
        offline=dict(type="bool", default=False),
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
    name = backend_name(module)
    current = get_backend(
        client,
        module.params["load_balancer_id"],
        module.params["backend_set_name"],
        name,
    )

    if state == "absent":
        if current is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_backend(module, client)
        module.exit_json(changed=True)
        return

    # state == present
    if current is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_backend(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    if needs_update(current, module):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_backend(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(current))


if __name__ == "__main__":
    main()
