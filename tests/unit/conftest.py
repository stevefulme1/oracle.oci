"""Shared pytest fixtures for OCI collection unit tests."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock

import pytest


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
