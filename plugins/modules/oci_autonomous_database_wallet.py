#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for downloading OCI Autonomous Database wallets."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_autonomous_database_wallet
short_description: Download an Autonomous Database wallet from OCI
description:
    - Download a client credentials (wallet) zip file for an Autonomous Database.
    - The wallet is required for connections to the Autonomous Database using
      mutual TLS (mTLS) authentication.
    - This is an action module with no state parameter. It always attempts to
      download and write the wallet file.
    - Uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    autonomous_database_id:
        description:
            - The OCID of the Autonomous Database to download the wallet for.
        type: str
        required: true
    password:
        description:
            - The password to encrypt the keys inside the wallet zip file.
            - Must be at least 8 characters long and include at least one letter
              and one digit or special character.
        type: str
        required: true
    dest:
        description:
            - The local filesystem path where the wallet zip file will be saved.
            - Parent directories must already exist.
        type: path
        required: true
    force:
        description:
            - Whether to overwrite the wallet file if it already exists at I(dest).
            - When C(false), the module will not download the wallet if the file
              already exists.
        type: bool
        default: false
    generate_type:
        description:
            - The type of wallet to generate.
            - C(SINGLE) generates a wallet for a single database.
            - C(ALL) generates a wallet for all databases in the ADB-D group.
        type: str
        choices:
            - SINGLE
            - ALL
        default: SINGLE
extends_documentation_fragment:
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Download ADB wallet to local path
  oracle.oci.oci_autonomous_database_wallet:
    autonomous_database_id: "ocid1.autonomousdatabase.oc1..example"
    password: "WalletPass123#"
    dest: "/tmp/adb_wallet.zip"

- name: Download wallet, overwriting if it already exists
  oracle.oci.oci_autonomous_database_wallet:
    autonomous_database_id: "ocid1.autonomousdatabase.oc1..example"
    password: "WalletPass123#"
    dest: "/opt/oracle/wallets/mydb_wallet.zip"
    force: true

- name: Download wallet for all databases in the group
  oracle.oci.oci_autonomous_database_wallet:
    autonomous_database_id: "ocid1.autonomousdatabase.oc1..example"
    password: "WalletPass123#"
    dest: "/tmp/adb_wallet_all.zip"
    generate_type: ALL
"""

RETURN = r"""
changed:
    description: Whether the wallet file was written.
    returned: always
    type: bool
dest:
    description: The local path where the wallet was saved.
    returned: on success
    type: str
    sample: "/tmp/adb_wallet.zip"
"""

import os

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import GenerateAutonomousDatabaseWalletDetails
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
)


def get_module_args():
    """Build argument spec for this module."""
    module_args = dict(
        autonomous_database_id=dict(type="str", required=True),
        password=dict(type="str", required=True, no_log=True),
        dest=dict(type="path", required=True),
        force=dict(type="bool", default=False),
        generate_type=dict(
            type="str",
            choices=["SINGLE", "ALL"],
            default="SINGLE",
        ),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def main():
    """Module entry point."""
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    params = module.params
    dest = params["dest"]

    # If file exists and force is not set, skip download
    if os.path.exists(dest) and not params["force"]:
        module.exit_json(
            changed=False,
            dest=dest,
            msg="Wallet file already exists. Use force=true to overwrite.",
        )
        return

    if module.check_mode:
        module.exit_json(changed=True, dest=dest)
        return

    client = create_service_client(module, DatabaseClient)

    wallet_details = GenerateAutonomousDatabaseWalletDetails(
        password=params["password"],
        generate_type=params["generate_type"],
    )

    try:
        response = call_with_retry(
            client.generate_autonomous_database_wallet,
            params["autonomous_database_id"],
            wallet_details,
        )
    except ServiceError as e:
        module.fail_json(
            msg="Failed to generate wallet: {0}".format(str(e)),
            status_code=e.status,
            code=e.code,
        )
        return

    # Write the response body (streaming content) to disk
    try:
        dest_dir = os.path.dirname(dest)
        if dest_dir and not os.path.isdir(dest_dir):
            module.fail_json(msg="Destination directory does not exist: {0}".format(dest_dir))
            return

        with open(dest, "wb") as f:
            for chunk in response.data.raw.stream(1024 * 1024, decode_content=True):
                f.write(chunk)
    except (IOError, OSError) as e:
        module.fail_json(msg="Failed to write wallet to {0}: {1}".format(dest, str(e)))
        return

    module.exit_json(changed=True, dest=dest)


if __name__ == "__main__":
    main()
