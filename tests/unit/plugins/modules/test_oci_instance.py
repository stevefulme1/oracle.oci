"""Unit tests for oracle.oci.oci_instance module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_instance"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_instance(
    display_name='test-instance',
    shape='VM.Standard.E4.Flex',
):
    """Return a mock OCI instance object."""
    instance = MagicMock()
    instance.display_name = 'test-instance'
    instance.shape = 'VM.Standard.E4.Flex'
    instance.id = "ocid1.test.oc1..testresource"
    instance.compartment_id = "ocid1.compartment.oc1..test"
    instance.lifecycle_state = "AVAILABLE"
    instance.freeform_tags = {}
    instance.defined_tags = {}
    return instance


@pytest.fixture
def instance_create_args(module_args):
    """Module args for creating a instance."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "availability_domain": 'Uocm:PHX-AD-1',
        "shape": 'VM.Standard.E4.Flex',
        "image_id": 'ocid1.image.oc1..test',
        "display_name": 'test-instance',
        "subnet_id": 'ocid1.subnet.oc1..test',
        "shape_config": None,
        "metadata": None,
        "platform_config": None,
        "source_details": None,
    })
    return module_args


class TestOciInstanceCreate:
    """Test instance creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_instance(self, mock_create_client, instance_create_args):
        """Creating a instance calls launch_instance."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_instance()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.launch_instance.return_value = mock_response

        module = MagicMock()
        module.params = instance_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        obj = OciInstance(module)
        result = obj.create_resource()

        mock_client.launch_instance.assert_called_once()


class TestOciInstanceDelete:
    """Test instance deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_instance(self, mock_create_client, module_args):
        """Deleting a instance calls terminate_instance."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "instance_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "shape": None,
            "image_id": None,
            "display_name": None,
            "subnet_id": None,
            "shape_config": None,
            "metadata": None,
            "platform_config": None,
            "source_details": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        resource = _build_instance()

        obj = OciInstance(module)
        obj.delete_resource(resource)

        mock_client.terminate_instance.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_instance_already_gone(self, mock_create_client, module_args):
        """When instance does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_instance.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "instance_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "shape": None,
            "image_id": None,
            "display_name": None,
            "subnet_id": None,
            "shape_config": None,
            "metadata": None,
            "platform_config": None,
            "source_details": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        obj = OciInstance(module)
        result = obj.get_resource()
        assert result is None


class TestOciInstanceUpdate:
    """Test instance update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_instance(self, mock_create_client, module_args):
        """Updating a instance calls update_instance."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "instance_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "shape": None,
            "image_id": None,
            "display_name": None,
            "subnet_id": None,
            "shape_config": None,
            "metadata": None,
            "platform_config": None,
            "source_details": None,
            "display_name": "updated-instance",
        })

        updated = _build_instance(display_name="updated-instance")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_instance.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        resource = _build_instance()

        obj = OciInstance(module)
        result = obj.update_resource(resource)

        mock_client.update_instance.assert_called_once()


class TestOciInstanceIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-instance',
            "shape": 'VM.Standard.E4.Flex',
            "availability_domain": None,
            "image_id": None,
            "subnet_id": None,
            "shape_config": None,
            "metadata": None,
            "platform_config": None,
            "source_details": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        resource = _build_instance()

        obj = OciInstance(module)
        assert not obj.needs_update(resource)
