"""Unit tests for oracle.oci.oci_nosql_table module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_nosql_table"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_nosql_table(
    name="test-table",
):
    """Return a mock OCI NoSQL table object."""
    table = MagicMock()
    table.name = name
    table.id = "ocid1.nosqltable.oc1..testresource"
    table.compartment_id = "ocid1.compartment.oc1..test"
    table.lifecycle_state = "ACTIVE"
    table.ddl_statement = "CREATE TABLE test-table (id INTEGER, name STRING, PRIMARY KEY(id))"
    table_limits = MagicMock()
    table_limits.max_read_units = 10
    table_limits.max_write_units = 10
    table_limits.max_storage_in_gbs = 1
    table.table_limits = table_limits
    table.freeform_tags = {}
    table.defined_tags = {}
    return table


@pytest.fixture
def nosql_table_create_args(module_args):
    """Module args for creating a NoSQL table."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "name": "test-table",
        "ddl_statement": "CREATE TABLE test-table (id INTEGER, name STRING, PRIMARY KEY(id))",
        "table_limits": {"max_read_units": 10, "max_write_units": 10, "max_storage_in_gbs": 1},
        "table_name_or_id": None,
    })
    return module_args


class TestOciNosqlTableCreate:
    """Test NoSQL table creation."""

    @patch(f"{MODULE_PATH}.TableLimits", lambda **kw: MagicMock(**kw))
    @patch(f"{MODULE_PATH}.CreateTableDetails", lambda **kw: MagicMock(**kw))
    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_nosql_table(self, mock_create_client, nosql_table_create_args):
        """Creating a NoSQL table calls create_table."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_nosql_table()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_table.return_value = mock_response

        module = MagicMock()
        module.params = nosql_table_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nosql_table import create_nosql_table
        result = create_nosql_table(module, mock_client)

        mock_client.create_table.assert_called_once()


class TestOciNosqlTableDelete:
    """Test NoSQL table deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_nosql_table(self, mock_create_client, module_args):
        """Deleting a NoSQL table calls delete_table."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "absent",
            "table_name_or_id": "ocid1.nosqltable.oc1..testresource",
            "compartment_id": None,
            "name": None,
            "ddl_statement": None,
            "table_limits": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_nosql_table()

        from ansible_collections.oracle.oci.plugins.modules.oci_nosql_table import delete_nosql_table
        delete_nosql_table(module, mock_client, resource)

        mock_client.delete_table.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_nosql_table_already_gone(self, mock_create_client, module_args):
        """When NoSQL table does not exist, get_nosql_table returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_table.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        from ansible_collections.oracle.oci.plugins.modules.oci_nosql_table import get_nosql_table
        result = get_nosql_table(mock_client, "ocid1.nosqltable.oc1..nonexistent")
        assert result is None


class TestOciNosqlTableUpdate:
    """Test NoSQL table update."""

    @patch(f"{MODULE_PATH}.TableLimits", lambda **kw: MagicMock(**kw))
    @patch(f"{MODULE_PATH}.UpdateTableDetails", lambda **kw: MagicMock(**kw))
    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_nosql_table(self, mock_create_client, module_args):
        """Updating a NoSQL table calls update_table."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "present",
            "table_name_or_id": "ocid1.nosqltable.oc1..testresource",
            "name": "test-table",
            "table_limits": {"max_read_units": 20, "max_write_units": 20, "max_storage_in_gbs": 2},
            "compartment_id": None,
            "ddl_statement": None,
        })

        updated = _build_nosql_table()
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_table.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_nosql_table()

        from ansible_collections.oracle.oci.plugins.modules.oci_nosql_table import update_nosql_table
        result = update_nosql_table(module, mock_client, resource)

        mock_client.update_table.assert_called_once()


class TestOciNosqlTableIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": "test-table",
            "table_limits": None,
            "ddl_statement": None,
            "table_name_or_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_nosql_table()

        from ansible_collections.oracle.oci.plugins.modules.oci_nosql_table import needs_update
        assert not needs_update(module.params, resource)
