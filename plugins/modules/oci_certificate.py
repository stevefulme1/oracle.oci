# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Certificate Management."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_certificate
short_description: Manage OCI certificates
description:
  - Create, update, and delete certificates in Oracle Cloud Infrastructure
    Certificates Management service.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the certificate resides.
      - Required when creating a new certificate.
    type: str
  certificate_id:
    description:
      - The OCID of the certificate.
      - Required for update and delete operations.
    type: str
  name:
    description:
      - A user-friendly name for the certificate.
      - Required when creating a new certificate.
    type: str
  certificate_config:
    description:
      - The certificate configuration details.
    type: dict
    suboptions:
      config_type:
        description:
          - The type of certificate configuration.
        type: str
        required: true
      cert_chain_pem:
        description:
          - The certificate chain in PEM format.
        type: str
      private_key_pem:
        description:
          - The private key in PEM format.
        type: str
      certificate_pem:
        description:
          - The certificate in PEM format.
        type: str
  state:
    description:
      - The desired state of the certificate.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a certificate with imported config
  oracle.oci.oci_certificate:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "my-cert"
    certificate_config:
      config_type: IMPORTED
      cert_chain_pem: "-----BEGIN CERTIFICATE-----..."
      private_key_pem: "-----BEGIN RSA PRIVATE KEY-----..."
      certificate_pem: "-----BEGIN CERTIFICATE-----..."
    state: present

- name: Delete a certificate
  oracle.oci.oci_certificate:
    certificate_id: "ocid1.certificate.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The certificate details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the certificate.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    name:
      description: The name of the certificate.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the certificate was created.
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
    from oci.certificates_management import CertificatesManagementClient
    from oci.certificates_management.models import (
        CreateCertificateDetails,
        UpdateCertificateDetails,
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


def get_resource(client, resource_id):
    """Get a certificate by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_certificate, resource_id)
        resource = response.data
        if resource.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return resource
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, name):
    """Find a certificate by compartment and name."""
    if not compartment_id or not name:
        return None
    resources = call_with_retry(
        client.list_certificates, compartment_id=compartment_id, name=name
    ).data
    items = resources.items if hasattr(resources, "items") else resources
    for r in items:
        if r.name == name and r.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_resource(client, r.id)
    return None


def create_resource(module, client):
    """Create a new certificate."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        name=module.params["name"],
    )
    cert_config = module.params.get("certificate_config")
    if cert_config:
        kwargs["certificate_config"] = cert_config
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateCertificateDetails(**kwargs)
    response = call_with_retry(client.create_certificate, details)
    resource = response.data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_certificate, resource.id,
            target_states={"ACTIVE"},
        )
    return resource


def update_resource(module, client, resource):
    """Update an existing certificate."""
    kwargs = {}
    cert_config = module.params.get("certificate_config")
    if cert_config is not None:
        kwargs["certificate_config"] = cert_config
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdateCertificateDetails(**kwargs)
    response = call_with_retry(client.update_certificate, resource.id, details)
    return response.data


def delete_resource(module, client, resource):
    """Delete a certificate."""
    call_with_retry(client.delete_certificate, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_certificate, resource.id,
            target_states={"DELETED", "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if the certificate needs updating."""
    if module.params.get("certificate_config") is not None:
        return True
    freeform_tags = module.params.get("freeform_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        return True
    defined_tags = module.params.get("defined_tags")
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        return True
    return False


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        certificate_id=dict(type="str"),
        name=dict(type="str"),
        certificate_config=dict(
            type="dict",
            options=dict(
                config_type=dict(type="str", required=True),
                cert_chain_pem=dict(type="str"),
                private_key_pem=dict(type="str", no_log=True),
                certificate_pem=dict(type="str"),
            ),
        ),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["certificate_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, CertificatesManagementClient)
    state = module.params["state"]
    resource_id = module.params.get("certificate_id")

    resource = None
    if resource_id:
        resource = get_resource(client, resource_id)
    elif module.params.get("compartment_id") and module.params.get("name"):
        resource = find_resource(client, module.params["compartment_id"], module.params["name"])

    if state == "absent":
        if resource is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, resource)
        module.exit_json(changed=True)
        return

    if resource is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    if needs_update(module, resource):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, resource)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(resource))


if __name__ == "__main__":
    main()
