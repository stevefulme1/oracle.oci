# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Service Connector Hub connectors."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_service_connector
short_description: Manage OCI Service Connector Hub connectors
description:
  - Create, update, and delete service connectors in OCI Service Connector Hub.
  - Service connectors move data between OCI services (e.g., Logging to Object Storage).
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment.
      - Required when creating.
    type: str
  service_connector_id:
    description:
      - The OCID of the service connector.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the service connector.
      - Required when creating.
    type: str
  source:
    description:
      - The source configuration for the service connector.
      - Required when creating.
    type: dict
    suboptions:
      kind:
        description: The type of source (e.g., logging, streaming).
        type: str
      log_sources:
        description: List of log source configurations.
        type: list
  target:
    description:
      - The target configuration for the service connector.
      - Required when creating.
    type: dict
    suboptions:
      kind:
        description: The type of target (e.g., objectStorage, streaming, functions, monitoring).
        type: str
      bucket_name:
        description: The target bucket name (for objectStorage target).
        type: str
      namespace:
        description: The target namespace (for objectStorage target).
        type: str
  tasks:
    description:
      - List of tasks (transformations) to apply to data in transit.
    type: list
    elements: dict
  freeform_tags:
    description:
      - Free-form tags for this resource.
    type: dict
  defined_tags:
    description:
      - Defined tags for this resource.
    type: dict
  state:
    description:
      - The desired state of the service connector.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a service connector from Logging to Object Storage
  oracle.oci.oci_service_connector:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "logs-to-object-storage"
    source:
      kind: logging
      log_sources:
        - compartment_id: "ocid1.compartment.oc1..example"
          log_group_id: "ocid1.loggroup.oc1..example"
    target:
      kind: objectStorage
      bucket_name: "log-archive"
      namespace: "mynamespace"
    state: present

- name: Delete a service connector
  oracle.oci.oci_service_connector:
    service_connector_id: "ocid1.serviceconnector.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The service connector details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the service connector.
      type: str
    display_name:
      description: The display name.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    source:
      description: The source configuration.
      type: dict
    target:
      description: The target configuration.
      type: dict
    lifecycle_state:
      description: The current lifecycle state.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.sch import ServiceConnectorClient
    from oci.sch.models import (
        CreateServiceConnectorDetails,
        UpdateServiceConnectorDetails,
        LoggingSourceDetails,
        LogSource,
        ObjectStorageTargetDetails,
        StreamingTargetDetails,
        FunctionsTargetDetails,
        MonitoringTargetDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def to_dict(resource):
    """Convert an OCI SDK resource to a serializable dict."""
    if resource is None:
        return {}
    result = {}
    for key, value in resource.__dict__.items():
        if key.startswith("_"):
            continue
        if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
            result[key] = to_dict(value)
        elif isinstance(value, list):
            result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
        else:
            result[key] = value
    return result


def build_source(source_param):
    """Build a source details object from module params."""
    if not source_param:
        return None
    kind = source_param.get("kind", "logging")
    if kind == "logging":
        log_sources = []
        for ls in source_param.get("log_sources", []):
            log_sources.append(LogSource(
                compartment_id=ls.get("compartment_id"),
                log_group_id=ls.get("log_group_id"),
                log_id=ls.get("log_id"),
            ))
        return LoggingSourceDetails(log_sources=log_sources)
    return None


def build_target(target_param):
    """Build a target details object from module params."""
    if not target_param:
        return None
    kind = target_param.get("kind", "objectStorage")
    if kind == "objectStorage":
        return ObjectStorageTargetDetails(
            bucket_name=target_param.get("bucket_name"),
            namespace=target_param.get("namespace"),
            object_name_prefix=target_param.get("object_name_prefix"),
        )
    if kind == "streaming":
        return StreamingTargetDetails(
            stream_id=target_param.get("stream_id"),
        )
    if kind == "functions":
        return FunctionsTargetDetails(
            function_id=target_param.get("function_id"),
        )
    if kind == "monitoring":
        return MonitoringTargetDetails(
            compartment_id=target_param.get("compartment_id"),
            metric_namespace=target_param.get("metric_namespace"),
            metric=target_param.get("metric"),
        )
    return None


def get_connector(client, service_connector_id):
    """Get a service connector by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_service_connector, service_connector_id)
        connector = response.data
        if connector.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return connector
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_connector(client, compartment_id, display_name):
    """Find a service connector by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    connectors = call_with_retry(
        client.list_service_connectors,
        compartment_id,
        display_name=display_name,
    ).data.items
    for c in connectors:
        if c.display_name == display_name and c.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_connector(client, c.id)
    return None


def create_connector(module, client):
    """Create a new service connector."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    details = CreateServiceConnectorDetails(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        source=build_source(module.params.get("source")),
        target=build_target(module.params.get("target")),
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    response = call_with_retry(client.create_service_connector, details)
    response.headers.get("opc-work-request-id")

    # Find the created connector
    connectors = call_with_retry(
        client.list_service_connectors,
        module.params["compartment_id"],
        display_name=module.params["display_name"],
    ).data.items
    for c in connectors:
        if c.display_name == module.params["display_name"]:
            if module.params.get("wait", True):
                return wait_for_resource(
                    module, client.get_service_connector, c.id, target_states={"ACTIVE"},
                )
            return get_connector(client, c.id)
    return None


def update_connector(module, client, connector):
    """Update an existing service connector."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("source") is not None:
        kwargs["source"] = build_source(module.params["source"])
    if module.params.get("target") is not None:
        kwargs["target"] = build_target(module.params["target"])
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return connector

    details = UpdateServiceConnectorDetails(**kwargs)
    call_with_retry(client.update_service_connector, connector.id, details)
    return get_connector(client, connector.id)


def delete_connector(module, client, connector):
    """Delete a service connector."""
    call_with_retry(client.delete_service_connector, connector.id)


def needs_update(module, connector):
    """Check if the service connector needs updating."""
    if module.params.get("display_name") is not None:
        if connector.display_name != module.params["display_name"]:
            return True
    if module.params.get("freeform_tags") is not None:
        if getattr(connector, "freeform_tags", None) != module.params["freeform_tags"]:
            return True
    if module.params.get("defined_tags") is not None:
        if getattr(connector, "defined_tags", None) != module.params["defined_tags"]:
            return True
    # Source and target changes always trigger update when provided
    if module.params.get("source") is not None or module.params.get("target") is not None:
        return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        service_connector_id=dict(type="str"),
        display_name=dict(type="str"),
        source=dict(type="dict"),
        target=dict(type="dict"),
        tasks=dict(type="list", elements="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name", "source", "target"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, ServiceConnectorClient)
    state = module.params.get("state", "present")
    service_connector_id = module.params.get("service_connector_id")

    # Get existing resource
    connector = None
    if service_connector_id:
        connector = get_connector(client, service_connector_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        connector = find_connector(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if connector is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_connector(module, client, connector)
        module.exit_json(changed=True)
        return

    # state == present
    if connector is None:
        if not module.params.get("compartment_id") or not module.params.get("display_name"):
            module.fail_json(msg="compartment_id, display_name, source, and target are required to create a connector.")
        if module.check_mode:
            module.exit_json(changed=True)
        connector = create_connector(module, client)
        module.exit_json(changed=True, resource=to_dict(connector))
        return

    if needs_update(module, connector):
        if module.check_mode:
            module.exit_json(changed=True)
        connector = update_connector(module, client, connector)
        module.exit_json(changed=True, resource=to_dict(connector))
        return

    module.exit_json(changed=False, resource=to_dict(connector))


def main():
    run_module()


if __name__ == "__main__":
    main()
