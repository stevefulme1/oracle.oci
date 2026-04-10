"""Shared pytest fixtures for OCI collection unit tests."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import sys
from unittest.mock import MagicMock

import pytest

# When the collection is checked out as ansible_collections/oracle/oci/,
# the grandparent of the collection root contains the ansible_collections
# namespace package.  Add it to sys.path so that imports like
# ``ansible_collections.oracle.oci.plugins...`` resolve during unit tests.
_collection_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
_namespace_root = os.path.abspath(os.path.join(_collection_root, os.pardir, os.pardir))
if os.path.isdir(os.path.join(_namespace_root, "ansible_collections")) and _namespace_root not in sys.path:
    sys.path.insert(0, _namespace_root)


@pytest.fixture
def module_args():
    """Return a base dict of OCI common module arguments."""
    return {
        "config_file_location": "~/.oci/config",
        "config_profile_name": "DEFAULT",
        "auth_type": "api_key",
        "tenancy": "ocid1.tenancy.oc1..testtenancy",
        "region": "us-phoenix-1",
        "api_user": "ocid1.user.oc1..testuser",
        "api_user_fingerprint": "aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99",
        "api_user_key_file": "/tmp/oci_test_key.pem",
        "api_user_key_pass_phrase": None,
        "wait": True,
        "wait_timeout": 1200,
        "wait_interval": 30,
        "freeform_tags": None,
        "defined_tags": None,
        "state": "present",
    }


@pytest.fixture
def mock_oci_client():
    """Factory fixture that returns a MagicMock configured as an OCI service client.

    Usage in tests:
        def test_something(mock_oci_client):
            client = mock_oci_client("ComputeClient")
            client.launch_instance.return_value = ...
    """

    def _factory(client_name: str = "GenericClient") -> MagicMock:
        client = MagicMock(name=client_name)
        return client

    return _factory
