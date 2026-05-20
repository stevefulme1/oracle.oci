"""Unit tests for oracle.oci.oci_mount_target module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_mount_target"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_mount_target(
    display_name='test-mt',
):
    """Return a mock OCI mount_target object."""
    mount_target = MagicMock()
    mount_target.display_name = 'test-mt'
    mount_target.id = "ocid1.test.oc1..testresource"
    mount_target.compartment_id = "ocid1.compartment.oc1..test"
    mount_target.lifecycle_state = "AVAILABLE"
    mount_target.freeform_tags = {}
    mount_target.defined_tags = {}
    return mount_target


@pytest.fixture
def mount_target_create_args(module_args):
    """Module args for creating a mount_target."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "availability_domain": 'Uocm:PHX-AD-1',
        "subnet_id": 'ocid1.subnet.oc1..test',
        "display_name": 'test-mt',
    })
    return module_args


class TestOciMountTargetCreate:
    """Test mount_target creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_mount_target(self, mock_create_client, mount_target_create_args):
        """Creating a mount_target calls create_mount_target."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_mount_target()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_mount_target.return_value = mock_response

        module = MagicMock()
        module.params = mount_target_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_mount_target import OciMountTarget
        obj = OciMountTarget(module)
        result = obj.create_resource()

        mock_client.create_mount_target.assert_called_once()


class TestOciMountTargetDelete:
    """Test mount_target deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_mount_target(self, mock_create_client, module_args):
        """Deleting a mount_target calls delete_mount_target."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "mount_target_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "subnet_id": None,
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_mount_target import OciMountTarget
        resource = _build_mount_target()

        obj = OciMountTarget(module)
        obj.delete_resource(resource)

        mock_client.delete_mount_target.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_mount_target_already_gone(self, mock_create_client, module_args):
        """When mount_target does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_mount_target.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "mount_target_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "subnet_id": None,
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_mount_target import OciMountTarget
        obj = OciMountTarget(module)
        result = obj.get_resource()
        assert result is None


class TestOciMountTargetUpdate:
    """Test mount_target update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_mount_target(self, mock_create_client, module_args):
        """Updating a mount_target calls update_mount_target."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "mount_target_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "subnet_id": None,
            "display_name": None,
            "display_name": "updated-mount_target",
        })

        updated = _build_mount_target(display_name="updated-mount_target")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_mount_target.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_mount_target import OciMountTarget
        resource = _build_mount_target()

        obj = OciMountTarget(module)
        result = obj.update_resource(resource)

        mock_client.update_mount_target.assert_called_once()


class TestOciMountTargetIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-mt',
            "availability_domain": None,
            "subnet_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_mount_target import OciMountTarget
        resource = _build_mount_target()

        obj = OciMountTarget(module)
        assert not obj.needs_update(resource)
