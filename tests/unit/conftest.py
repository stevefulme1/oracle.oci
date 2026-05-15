"""Shared pytest fixtures for OCI collection unit tests."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import sys
import types
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# 1.  Provide a mock ``oci`` SDK if the real one is not installed.
#     This must happen before any collection code is imported so that
#     ``try: import oci`` blocks see HAS_OCI_SDK = True.
# ---------------------------------------------------------------------------
try:
    import oci as _real_oci  # noqa: F401
except ImportError:
    class _ServiceError(Exception):
        """Minimal stand-in for oci.exceptions.ServiceError."""
        def __init__(self, status=None, code=None, message=None, headers=None, **kwargs):
            self.status = status
            self.code = code
            self.message = message
            self.headers = headers or {}
            super().__init__(message)

    class _InvalidConfig(Exception):
        """Stand-in for oci.exceptions.InvalidConfig."""

    # Build the ``oci`` package tree that collection code imports from.
    _oci = types.ModuleType("oci")
    _oci.__path__ = []
    _oci.__package__ = "oci"

    _oci_exceptions = types.ModuleType("oci.exceptions")
    _oci_exceptions.ServiceError = _ServiceError
    _oci_exceptions.InvalidConfig = _InvalidConfig
    _oci.exceptions = _oci_exceptions

    _oci_config = MagicMock()
    _oci.config = _oci_config

    _oci_auth = types.ModuleType("oci.auth")
    _oci_auth.__path__ = []
    _oci_auth_signers = MagicMock()
    _oci_auth.signers = _oci_auth_signers
    _oci.auth = _oci_auth

    _oci_core = types.ModuleType("oci.core")
    _oci_core.__path__ = []
    _oci_core.ComputeClient = MagicMock
    _oci_core.VirtualNetworkClient = MagicMock
    _oci.core = _oci_core

    class _OciModelsModule(types.ModuleType):
        """Auto-creates simple data classes for any oci.*.models.* access."""
        def __getattr__(self, name):
            # Dynamically create a class that stores **kwargs as attributes.
            cls = type(name, (), {"__init__": lambda self, **kw: self.__dict__.update(kw)})
            setattr(self, name, cls)
            return cls

    _oci_core_models = _OciModelsModule("oci.core.models")
    _oci_core.models = _oci_core_models

    # oci.object_storage
    _oci_object_storage = types.ModuleType("oci.object_storage")
    _oci_object_storage.__path__ = []
    _oci_object_storage.ObjectStorageClient = MagicMock
    _oci.object_storage = _oci_object_storage

    _oci_object_storage_models = _OciModelsModule("oci.object_storage.models")
    _oci_object_storage.models = _oci_object_storage_models

    # oci.identity
    _oci_identity = types.ModuleType("oci.identity")
    _oci_identity.__path__ = []
    _oci_identity.IdentityClient = MagicMock
    _oci.identity = _oci_identity

    _oci_identity_models = _OciModelsModule("oci.identity.models")
    _oci_identity.models = _oci_identity_models

    # oci.load_balancer
    _oci_load_balancer = types.ModuleType("oci.load_balancer")
    _oci_load_balancer.__path__ = []
    _oci_load_balancer.LoadBalancerClient = MagicMock
    _oci.load_balancer = _oci_load_balancer

    _oci_load_balancer_models = _OciModelsModule("oci.load_balancer.models")
    _oci_load_balancer.models = _oci_load_balancer_models

    for _name, _mod in [
        ("oci", _oci),
        ("oci.exceptions", _oci_exceptions),
        ("oci.config", _oci_config),
        ("oci.auth", _oci_auth),
        ("oci.auth.signers", _oci_auth_signers),
        ("oci.core", _oci_core),
        ("oci.core.models", _oci_core_models),
        ("oci.object_storage", _oci_object_storage),
        ("oci.object_storage.models", _oci_object_storage_models),
        ("oci.identity", _oci_identity),
        ("oci.identity.models", _oci_identity_models),
        ("oci.load_balancer", _oci_load_balancer),
        ("oci.load_balancer.models", _oci_load_balancer_models),
    ]:
        sys.modules[_name] = _mod


# ---------------------------------------------------------------------------
# 2.  Set up the ansible_collections.stevefulme1.oci_cloud namespace package so that
#     collection imports work from a standalone checkout or CI.
# ---------------------------------------------------------------------------
_collection_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

_namespace_root = os.path.abspath(os.path.join(_collection_root, os.pardir, os.pardir))
if os.path.isdir(os.path.join(_namespace_root, "ansible_collections")) and _namespace_root not in sys.path:
    sys.path.insert(0, _namespace_root)

try:
    import ansible_collections.stevefulme1.oci_cloud  # noqa: F401  # pylint: disable=unused-import
except (ImportError, ModuleNotFoundError):
    for _pkg_name in ("ansible_collections", "ansible_collections.stevefulme1"):
        if _pkg_name not in sys.modules:
            _pkg = types.ModuleType(_pkg_name)
            _pkg.__path__ = []
            _pkg.__package__ = _pkg_name
            sys.modules[_pkg_name] = _pkg

    _oci_mod = types.ModuleType("ansible_collections.stevefulme1.oci_cloud")
    _oci_mod.__path__ = [_collection_root]
    _oci_mod.__package__ = "ansible_collections.stevefulme1.oci_cloud"
    sys.modules["ansible_collections.stevefulme1.oci_cloud"] = _oci_mod

    sys.modules["ansible_collections"].stevefulme1 = sys.modules["ansible_collections.stevefulme1"]
    sys.modules["ansible_collections.stevefulme1"].oci_cloud = _oci_mod


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
