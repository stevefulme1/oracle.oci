"""Unit tests for oracle.oci.oci_mysql_db_system module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_mysql_db_system"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_mysql_db_system(
    display_name="My MySQL DB",
    shape_name="MySQL.VM.Standard.E4.1.8GB",
):
    """Return a mock OCI MySQL DB System object."""
    db_system = MagicMock()
    db_system.display_name = display_name
    db_system.shape_name = shape_name
    db_system.id = "ocid1.mysqldbsystem.oc1..testresource"
    db_system.compartment_id = "ocid1.compartment.oc1..test"
    db_system.availability_domain = "Uocm:PHX-AD-1"
    db_system.subnet_id = "ocid1.subnet.oc1..test"
    db_system.lifecycle_state = "ACTIVE"
    db_system.data_storage_size_in_gbs = 50
    db_system.description = "Test MySQL DB"
    db_system.freeform_tags = {}
    db_system.defined_tags = {}
    return db_system


@pytest.fixture
def mysql_db_system_create_args(module_args):
    """Module args for creating a MySQL DB System."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "display_name": "My MySQL DB",
        "admin_username": "admin",
        "admin_password": "TestPass#1",
        "shape_name": "MySQL.VM.Standard.E4.1.8GB",
        "subnet_id": "ocid1.subnet.oc1..test",
        "availability_domain": "Uocm:PHX-AD-1",
        "data_storage_size_in_gbs": 50,
        "mysql_version": None,
        "description": "Test MySQL DB",
        "db_system_id": None,
    })
    return module_args


class TestOciMysqlDbSystemCreate:
    """Test MySQL DB System creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_mysql_db_system(self, mock_create_client, mysql_db_system_create_args):
        """Creating a MySQL DB System calls create_db_system."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_mysql_db_system()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_db_system.return_value = mock_response

        module = MagicMock()
        module.params = mysql_db_system_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_mysql_db_system import create_mysql_db_system
        result = create_mysql_db_system(module, mock_client)

        mock_client.create_db_system.assert_called_once()


class TestOciMysqlDbSystemDelete:
    """Test MySQL DB System deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_mysql_db_system(self, mock_create_client, module_args):
        """Deleting a MySQL DB System calls delete_db_system."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "absent",
            "db_system_id": "ocid1.mysqldbsystem.oc1..testresource",
            "compartment_id": None,
            "display_name": None,
            "admin_username": None,
            "admin_password": None,
            "shape_name": None,
            "subnet_id": None,
            "availability_domain": None,
            "data_storage_size_in_gbs": None,
            "mysql_version": None,
            "description": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_mysql_db_system()

        from ansible_collections.oracle.oci.plugins.modules.oci_mysql_db_system import delete_mysql_db_system
        delete_mysql_db_system(module, mock_client, resource)

        mock_client.delete_db_system.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_mysql_db_system_already_gone(self, mock_create_client, module_args):
        """When MySQL DB System does not exist, get returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_db_system.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        from ansible_collections.oracle.oci.plugins.modules.oci_mysql_db_system import get_mysql_db_system
        result = get_mysql_db_system(mock_client, "ocid1.mysqldbsystem.oc1..nonexistent")
        assert result is None


class TestOciMysqlDbSystemUpdate:
    """Test MySQL DB System update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_mysql_db_system(self, mock_create_client, module_args):
        """Updating a MySQL DB System calls update_db_system."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "present",
            "db_system_id": "ocid1.mysqldbsystem.oc1..testresource",
            "display_name": "Updated MySQL DB",
            "compartment_id": None,
            "admin_username": None,
            "admin_password": None,
            "shape_name": None,
            "subnet_id": None,
            "availability_domain": None,
            "data_storage_size_in_gbs": None,
            "mysql_version": None,
            "description": None,
        })

        updated = _build_mysql_db_system(display_name="Updated MySQL DB")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_db_system.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_mysql_db_system()

        from ansible_collections.oracle.oci.plugins.modules.oci_mysql_db_system import update_mysql_db_system
        result = update_mysql_db_system(module, mock_client, resource)

        mock_client.update_db_system.assert_called_once()


class TestOciMysqlDbSystemIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": "My MySQL DB",
            "description": None,
            "db_system_id": None,
            "compartment_id": None,
            "admin_username": None,
            "admin_password": None,
            "shape_name": None,
            "subnet_id": None,
            "availability_domain": None,
            "data_storage_size_in_gbs": None,
            "mysql_version": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_mysql_db_system()

        from ansible_collections.oracle.oci.plugins.modules.oci_mysql_db_system import needs_update
        assert not needs_update(module.params, resource)
