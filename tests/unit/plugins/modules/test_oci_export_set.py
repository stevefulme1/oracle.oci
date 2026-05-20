"""Unit tests for oracle.oci.oci_export_set module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_export_set"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_export_set(
    display_name="my-export-set",
    max_fs_stat_bytes=None,
    max_fs_stat_files=None,
):
    """Return a mock OCI export set object."""
    export_set = MagicMock()
    export_set.display_name = display_name
    export_set.max_fs_stat_bytes = max_fs_stat_bytes
    export_set.max_fs_stat_files = max_fs_stat_files
    export_set.id = "ocid1.exportset.oc1..testresource"
    export_set.compartment_id = "ocid1.compartment.oc1..test"
    export_set.lifecycle_state = "ACTIVE"
    export_set.freeform_tags = {}
    export_set.defined_tags = {}
    return export_set


@pytest.fixture
def export_set_args(module_args):
    """Module args for managing an export set."""
    module_args.update({
        "export_set_id": "ocid1.exportset.oc1..testresource",
        "display_name": "my-export-set",
        "max_fs_stat_bytes": None,
        "max_fs_stat_files": None,
    })
    return module_args


class TestOciExportSetUpdate:
    """Test export set update (export sets are update-only, no create/delete)."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_export_set(self, mock_create_client, module_args):
        """Updating an export set calls update_export_set."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "export_set_id": "ocid1.exportset.oc1..testresource",
            "display_name": "renamed-export-set",
            "max_fs_stat_bytes": None,
            "max_fs_stat_files": None,
        })

        updated = _build_export_set(display_name="renamed-export-set")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_export_set.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_export_set()

        from ansible_collections.oracle.oci.plugins.modules.oci_export_set import update_export_set
        result = update_export_set(module, mock_client, resource)

        mock_client.update_export_set.assert_called_once()


class TestOciExportSetGetResource:
    """Test export set get."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_get_export_set(self, mock_create_client, module_args):
        """Getting an export set calls get_export_set."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        resource = _build_export_set()
        mock_response = MagicMock()
        mock_response.data = resource
        mock_client.get_export_set.return_value = mock_response

        from ansible_collections.oracle.oci.plugins.modules.oci_export_set import get_export_set
        result = get_export_set(mock_client, "ocid1.exportset.oc1..testresource")

        mock_client.get_export_set.assert_called_once()
        assert result.display_name == "my-export-set"

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_get_export_set_not_found(self, mock_create_client, module_args):
        """When export set does not exist, get_export_set returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_export_set.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        from ansible_collections.oracle.oci.plugins.modules.oci_export_set import get_export_set
        result = get_export_set(mock_client, "ocid1.exportset.oc1..nonexistent")
        assert result is None


class TestOciExportSetIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "export_set_id": "ocid1.exportset.oc1..testresource",
            "display_name": "my-export-set",
            "max_fs_stat_bytes": None,
            "max_fs_stat_files": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_export_set()

        from ansible_collections.oracle.oci.plugins.modules.oci_export_set import needs_update
        assert not needs_update(module, resource)
