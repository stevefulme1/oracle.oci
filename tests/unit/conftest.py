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

    # oci.key_management
    _oci_key_management = types.ModuleType("oci.key_management")
    _oci_key_management.__path__ = []
    _oci_key_management.KmsManagementClient = MagicMock
    _oci_key_management.KmsVaultClient = MagicMock
    _oci.key_management = _oci_key_management

    _oci_key_management_models = _OciModelsModule("oci.key_management.models")
    _oci_key_management.models = _oci_key_management_models

    # oci.dns
    _oci_dns = types.ModuleType("oci.dns")
    _oci_dns.__path__ = []
    _oci_dns.DnsClient = MagicMock
    _oci.dns = _oci_dns

    _oci_dns_models = _OciModelsModule("oci.dns.models")
    _oci_dns.models = _oci_dns_models

    # oci.database
    _oci_database = types.ModuleType("oci.database")
    _oci_database.__path__ = []
    _oci_database.DatabaseClient = MagicMock
    _oci.database = _oci_database

    _oci_database_models = _OciModelsModule("oci.database.models")
    _oci_database.models = _oci_database_models

    # oci.monitoring
    _oci_monitoring = types.ModuleType("oci.monitoring")
    _oci_monitoring.__path__ = []
    _oci_monitoring.MonitoringClient = MagicMock
    _oci.monitoring = _oci_monitoring

    _oci_monitoring_models = _OciModelsModule("oci.monitoring.models")
    _oci_monitoring.models = _oci_monitoring_models

    # oci.logging
    _oci_logging = types.ModuleType("oci.logging")
    _oci_logging.__path__ = []
    _oci_logging.LoggingManagementClient = MagicMock
    _oci.logging = _oci_logging

    _oci_logging_models = _OciModelsModule("oci.logging.models")
    _oci_logging.models = _oci_logging_models

    # oci.ons (Oracle Notification Service)
    _oci_ons = types.ModuleType("oci.ons")
    _oci_ons.__path__ = []
    _oci_ons.NotificationControlPlaneClient = MagicMock
    _oci.ons = _oci_ons

    _oci_ons_models = _OciModelsModule("oci.ons.models")
    _oci_ons.models = _oci_ons_models

    # oci.file_storage
    _oci_file_storage = types.ModuleType("oci.file_storage")
    _oci_file_storage.__path__ = []
    _oci_file_storage.FileStorageClient = MagicMock
    _oci.file_storage = _oci_file_storage

    _oci_file_storage_models = _OciModelsModule("oci.file_storage.models")
    _oci_file_storage.models = _oci_file_storage_models

    # oci.mysql
    _oci_mysql = types.ModuleType("oci.mysql")
    _oci_mysql.__path__ = []
    _oci_mysql.DbSystemClient = MagicMock
    _oci.mysql = _oci_mysql

    _oci_mysql_models = _OciModelsModule("oci.mysql.models")
    _oci_mysql.models = _oci_mysql_models

    # oci.nosql
    _oci_nosql = types.ModuleType("oci.nosql")
    _oci_nosql.__path__ = []
    _oci_nosql.NosqlClient = MagicMock
    _oci.nosql = _oci_nosql

    _oci_nosql_models = _OciModelsModule("oci.nosql.models")
    _oci_nosql.models = _oci_nosql_models

    # oci.vault
    _oci_vault = types.ModuleType("oci.vault")
    _oci_vault.__path__ = []
    _oci_vault.VaultsClient = MagicMock
    _oci.vault = _oci_vault

    _oci_vault_models = _OciModelsModule("oci.vault.models")
    _oci_vault.models = _oci_vault_models

    # oci.container_engine (OKE)
    _oci_container_engine = types.ModuleType("oci.container_engine")
    _oci_container_engine.__path__ = []
    _oci_container_engine.ContainerEngineClient = MagicMock
    _oci.container_engine = _oci_container_engine

    _oci_container_engine_models = _OciModelsModule("oci.container_engine.models")
    _oci_container_engine.models = _oci_container_engine_models

    # oci.pagination
    _oci_pagination = MagicMock()
    _oci.pagination = _oci_pagination

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
        ("oci.key_management", _oci_key_management),
        ("oci.key_management.models", _oci_key_management_models),
        ("oci.dns", _oci_dns),
        ("oci.dns.models", _oci_dns_models),
        ("oci.database", _oci_database),
        ("oci.database.models", _oci_database_models),
        ("oci.monitoring", _oci_monitoring),
        ("oci.monitoring.models", _oci_monitoring_models),
        ("oci.logging", _oci_logging),
        ("oci.logging.models", _oci_logging_models),
        ("oci.ons", _oci_ons),
        ("oci.ons.models", _oci_ons_models),
        ("oci.file_storage", _oci_file_storage),
        ("oci.file_storage.models", _oci_file_storage_models),
        ("oci.mysql", _oci_mysql),
        ("oci.mysql.models", _oci_mysql_models),
        ("oci.nosql", _oci_nosql),
        ("oci.nosql.models", _oci_nosql_models),
        ("oci.vault", _oci_vault),
        ("oci.vault.models", _oci_vault_models),
        ("oci.container_engine", _oci_container_engine),
        ("oci.container_engine.models", _oci_container_engine_models),
        ("oci.pagination", _oci_pagination),
    ]:
        sys.modules[_name] = _mod


# ---------------------------------------------------------------------------
# 2.  Set up the ansible_collections.oracle.oci namespace package so that
#     collection imports work from a standalone checkout or CI.
# ---------------------------------------------------------------------------
_collection_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

# When the repo is checked out inside an ansible_collections/oracle/oci/
# directory tree (e.g. CI), the grandparent provides the namespace package.
_namespace_root = os.path.abspath(os.path.join(_collection_root, os.pardir, os.pardir))
if os.path.isdir(os.path.join(_namespace_root, "ansible_collections")) and _namespace_root not in sys.path:
    sys.path.insert(0, _namespace_root)

# Try importing; if it fails, build the namespace synthetically.
try:
    import ansible_collections.oracle.oci  # noqa: F401  # pylint: disable=unused-import
except (ImportError, ModuleNotFoundError):
    for _pkg_name in ("ansible_collections", "ansible_collections.oracle"):
        if _pkg_name not in sys.modules:
            _pkg = types.ModuleType(_pkg_name)
            _pkg.__path__ = []
            _pkg.__package__ = _pkg_name
            sys.modules[_pkg_name] = _pkg

    _oci_mod = types.ModuleType("ansible_collections.oracle.oci")
    _oci_mod.__path__ = [_collection_root]
    _oci_mod.__package__ = "ansible_collections.oracle.oci"
    sys.modules["ansible_collections.oracle.oci"] = _oci_mod

    sys.modules["ansible_collections"].oracle = sys.modules["ansible_collections.oracle"]
    sys.modules["ansible_collections.oracle"].oci = _oci_mod

    # Also register stevefulme1.oci_cloud as an alias so that ``from
    # ansible_collections.stevefulme1.oci_cloud.plugins...`` resolves to the
    # same tree.  Several modules still reference the old namespace.
    if "ansible_collections.stevefulme1" not in sys.modules:
        _sn = types.ModuleType("ansible_collections.stevefulme1")
        _sn.__path__ = []
        _sn.__package__ = "ansible_collections.stevefulme1"
        sys.modules["ansible_collections.stevefulme1"] = _sn
        sys.modules["ansible_collections"].stevefulme1 = _sn

    _oci_cloud_mod = types.ModuleType("ansible_collections.stevefulme1.oci_cloud")
    _oci_cloud_mod.__path__ = [_collection_root]
    _oci_cloud_mod.__package__ = "ansible_collections.stevefulme1.oci_cloud"
    sys.modules["ansible_collections.stevefulme1.oci_cloud"] = _oci_cloud_mod
    sys.modules["ansible_collections.stevefulme1"].oci_cloud = _oci_cloud_mod


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
