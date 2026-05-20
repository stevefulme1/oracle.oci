"""Unit tests for oracle.oci.oci_db_system module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_db_system"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_db_system(
    display_name="My DB System",
    hostname="mydbhost",
    shape="VM.Standard2.1",
):
    """Return a mock OCI DB System object."""
    db_system = MagicMock()
    db_system.display_name = display_name
    db_system.hostname = hostname
    db_system.shape = shape
    db_system.id = "ocid1.dbsystem.oc1..testresource"
    db_system.compartment_id = "ocid1.compartment.oc1..test"
    db_system.availability_domain = "Uocm:PHX-AD-1"
    db_system.subnet_id = "ocid1.subnet.oc1..test"
    db_system.lifecycle_state = "AVAILABLE"
    db_system.ssh_public_keys = ["ssh-rsa AAAA..."]
    db_system.cpu_core_count = 1
    db_system.data_storage_size_in_gbs = 256
    db_system.freeform_tags = {}
    db_system.defined_tags = {}
    return db_system


@pytest.fixture
def db_system_create_args(module_args):
    """Module args for creating a DB System."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "availability_domain": "Uocm:PHX-AD-1",
        "shape": "VM.Standard2.1",
        "ssh_public_keys": ["ssh-rsa AAAA..."],
        "subnet_id": "ocid1.subnet.oc1..test",
        "hostname": "mydbhost",
        "display_name": "My DB System",
        "db_home": {"db_version": "19.0.0.0", "database": {"admin_password": "TestPass#1", "db_name": "testdb"}},
        "cpu_core_count": 1,
        "node_count": 1,
        "data_storage_size_in_gbs": 256,
        "db_system_id": None,
    })
    return module_args


class TestOciDbSystemCreate:
    """Test DB System creation."""

    @patch(f"{MODULE_PATH}.LaunchDbSystemDetails", lambda **kw: MagicMock(**kw))
    @patch(f"{MODULE_PATH}.CreateDbHomeDetails", lambda **kw: MagicMock(**kw))
    @patch(f"{MODULE_PATH}.CreateDatabaseDetails", lambda **kw: MagicMock(**kw))
    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_db_system(self, mock_create_client, db_system_create_args):
        """Creating a DB System calls launch_db_system."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_db_system()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.launch_db_system.return_value = mock_response

        module = MagicMock()
        module.params = db_system_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_db_system import create_db_system
        result = create_db_system(module, mock_client)

        mock_client.launch_db_system.assert_called_once()


class TestOciDbSystemDelete:
    """Test DB System deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_db_system(self, mock_create_client, module_args):
        """Deleting a DB System calls terminate_db_system."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "absent",
            "db_system_id": "ocid1.dbsystem.oc1..testresource",
            "compartment_id": None,
            "availability_domain": None,
            "shape": None,
            "ssh_public_keys": None,
            "subnet_id": None,
            "hostname": None,
            "display_name": None,
            "db_home": None,
            "cpu_core_count": None,
            "node_count": None,
            "data_storage_size_in_gbs": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_db_system()

        from ansible_collections.oracle.oci.plugins.modules.oci_db_system import terminate_db_system
        terminate_db_system(module, mock_client, resource)

        mock_client.terminate_db_system.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_db_system_already_gone(self, mock_create_client, module_args):
        """When DB System does not exist, get_db_system returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_db_system.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        from ansible_collections.oracle.oci.plugins.modules.oci_db_system import get_db_system
        result = get_db_system(mock_client, "ocid1.dbsystem.oc1..nonexistent")
        assert result is None


class TestOciDbSystemUpdate:
    """Test DB System update."""

    @patch(f"{MODULE_PATH}.UpdateDbSystemDetails", lambda **kw: MagicMock(**kw))
    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_db_system(self, mock_create_client, module_args):
        """Updating a DB System calls update_db_system."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "present",
            "db_system_id": "ocid1.dbsystem.oc1..testresource",
            "display_name": "Updated DB System",
            "compartment_id": None,
            "availability_domain": None,
            "shape": None,
            "ssh_public_keys": None,
            "subnet_id": None,
            "hostname": None,
            "db_home": None,
            "cpu_core_count": None,
            "node_count": None,
            "data_storage_size_in_gbs": None,
        })

        updated = _build_db_system(display_name="Updated DB System")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_db_system.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_db_system()

        from ansible_collections.oracle.oci.plugins.modules.oci_db_system import update_db_system
        result = update_db_system(module, mock_client, resource)

        mock_client.update_db_system.assert_called_once()


class TestOciDbSystemIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": "My DB System",
            "ssh_public_keys": None,
            "cpu_core_count": None,
            "data_storage_size_in_gbs": None,
            "db_system_id": None,
            "compartment_id": None,
            "availability_domain": None,
            "shape": None,
            "subnet_id": None,
            "hostname": None,
            "db_home": None,
            "node_count": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_db_system()

        from ansible_collections.oracle.oci.plugins.modules.oci_db_system import needs_update
        assert not needs_update(module.params, resource)
