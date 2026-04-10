# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    """Common documentation fragment for OCI modules."""

    DOCUMENTATION = r"""
options:
  config_file_location:
    description:
      - Path to the OCI configuration file.
    type: str
    default: ~/.oci/config
  config_profile_name:
    description:
      - The profile name in the OCI configuration file.
    type: str
    default: DEFAULT
  auth_type:
    description:
      - The authentication method to use.
    type: str
    default: api_key
    choices:
      - api_key
      - instance_principal
      - resource_principal
      - session_token
  tenancy:
    description:
      - The OCID of the tenancy.
      - Required for API key authentication if not set in config file.
    type: str
  region:
    description:
      - The OCI region to use for API calls.
    type: str
  api_user:
    description:
      - The OCID of the user for API key authentication.
    type: str
  api_user_fingerprint:
    description:
      - The fingerprint of the API signing key.
    type: str
  api_user_key_file:
    description:
      - The path to the private key file used for API key authentication.
    type: str
  api_user_key_pass_phrase:
    description:
      - The passphrase for the private key, if encrypted.
    type: str
  wait:
    description:
      - Whether to wait for the resource to reach the desired state.
    type: bool
    default: true
  wait_timeout:
    description:
      - Maximum time in seconds to wait for resource state changes.
    type: int
    default: 1200
  wait_interval:
    description:
      - Time in seconds between polling attempts when waiting.
    type: int
    default: 30
  freeform_tags:
    description:
      - Free-form tags for this resource.
    type: dict
  defined_tags:
    description:
      - Defined tags for this resource.
    type: dict
"""
