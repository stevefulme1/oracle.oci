"""Unit tests for oracle.oci.oci_instance module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_instance"
AUTH_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_auth"
WAIT_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_wait"


def _build_instance(
    instance_id="ocid1.instance.oc1.phx.test1",
    display_name="test-instance",
    lifecycle_state="RUNNING",
    shape="VM.Standard.E4.Flex",
    availability_domain="Uocm:PHX-AD-1",
    compartment_id="ocid1.compartment.oc1..test",
):
    """Return a mock OCI instance object."""
    instance = MagicMock()
    instance.id = instance_id
    instance.display_name = display_name
    instance.lifecycle_state = lifecycle_state
    instance.shape = shape
    instance.availability_domain = availability_domain
    instance.compartment_id = compartment_id
    instance.freeform_tags = {}
    instance.defined_tags = {}
    instance.metadata = {}
    return instance


@pytest.fixture
def instance_create_args(module_args):
    """Module args for creating an instance."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "availability_domain": "Uocm:PHX-AD-1",
        "shape": "VM.Standard.E4.Flex",
        "image_id": "ocid1.image.oc1.phx.test",
        "subnet_id": "ocid1.subnet.oc1.phx.test",
        "display_name": "test-instance",
        "shape_config": None,
        "metadata": None,
        "instance_id": None,
    })
    return module_args


class TestOciInstanceArgValidation:
    """Test module argument validation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_state_absent_requires_instance_id(self, mock_create_client, module_args):
        """Deleting an instance requires instance_id."""
        from ansible.module_utils import basic

        module_args.update({
            "state": "absent",
            "instance_id": None,
            "compartment_id": None,
            "availability_domain": None,
            "shape": None,
            "image_id": None,
            "subnet_id": None,
            "display_name": None,
            "shape_config": None,
            "metadata": None,
        })

        basic._ANSIBLE_ARGS = None
        with pytest.raises(SystemExit):
            with patch.object(basic, "_ANSIBLE_ARGS", None):
                from ansible_collections.oracle.oci.plugins.modules.oci_instance import main
                args_str = str(module_args).replace("'", '"')
                args_str = args_str.replace("None", "null")
                args_str = args_str.replace("True", "true")
                args_str = args_str.replace("False", "false")
                args_json = '{"ANSIBLE_MODULE_ARGS": ' + args_str + '}'
                with patch.object(basic, "_ANSIBLE_ARGS", args_json.encode()):
                    main()


class TestOciInstanceCreate:
    """Test instance creation."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{WAIT_PATH}.call_with_retry")
    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_instance(self, mock_create_client, mock_call_retry, mock_wait, instance_create_args):
        """Creating an instance calls launch_instance and waits for RUNNING."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        launched_instance = _build_instance(lifecycle_state="PROVISIONING")
        mock_response = MagicMock()
        mock_response.data = launched_instance
        mock_call_retry.return_value = mock_response

        running_instance = _build_instance(lifecycle_state="RUNNING")
        mock_wait.return_value = running_instance

        # Mock get_instance to return 404 (resource not found = needs creation)
        import oci.exceptions
        mock_client.get_instance.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance

        module = MagicMock()
        module.params = instance_create_args
        module.check_mode = False

        oci_inst = OciInstance(module)
        result = oci_inst.create_resource()

        mock_call_retry.assert_called_once()
        call_args = mock_call_retry.call_args
        assert call_args[0][0] == mock_client.launch_instance
        assert result.lifecycle_state == "RUNNING"

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{WAIT_PATH}.call_with_retry")
    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_instance_with_shape_config(
        self, mock_create_client, mock_call_retry, mock_wait, instance_create_args,
    ):
        """Creating a flex instance passes shape_config details."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        instance_create_args["shape_config"] = {"ocpus": 2, "memory_in_gbs": 32}

        launched = _build_instance(lifecycle_state="PROVISIONING")
        mock_response = MagicMock()
        mock_response.data = launched
        mock_call_retry.return_value = mock_response
        mock_wait.return_value = _build_instance()

        module = MagicMock()
        module.params = instance_create_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        oci_inst = OciInstance(module)
        oci_inst.create_resource()

        launch_details = mock_call_retry.call_args[0][1]
        assert launch_details.shape_config is not None


class TestOciInstanceDelete:
    """Test instance termination."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{WAIT_PATH}.call_with_retry")
    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_instance(self, mock_create_client, mock_call_retry, mock_wait, module_args):
        """Deleting an instance calls terminate_instance."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "instance_id": "ocid1.instance.oc1.phx.test1",
            "state": "absent",
            "compartment_id": None,
            "availability_domain": None,
            "shape": None,
            "image_id": None,
            "subnet_id": None,
            "display_name": None,
            "shape_config": None,
            "metadata": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        resource = _build_instance()

        oci_inst = OciInstance(module)
        oci_inst.delete_resource(resource)

        mock_call_retry.assert_called_once()
        assert mock_call_retry.call_args[0][0] == mock_client.terminate_instance
        assert mock_call_retry.call_args[0][1] == resource.id


class TestOciInstanceUpdate:
    """Test instance update."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{WAIT_PATH}.call_with_retry")
    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_display_name(self, mock_create_client, mock_call_retry, mock_wait, module_args):
        """Updating display_name calls update_instance."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "instance_id": "ocid1.instance.oc1.phx.test1",
            "display_name": "renamed-instance",
            "compartment_id": None,
            "availability_domain": None,
            "shape": None,
            "image_id": None,
            "subnet_id": None,
            "shape_config": None,
            "metadata": None,
        })

        updated = _build_instance(display_name="renamed-instance")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_call_retry.return_value = mock_response
        mock_wait.return_value = updated

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        resource = _build_instance(display_name="old-name")

        oci_inst = OciInstance(module)
        result = oci_inst.update_resource(resource)

        mock_call_retry.assert_called_once()
        assert mock_call_retry.call_args[0][0] == mock_client.update_instance
        assert result.display_name == "renamed-instance"


class TestOciInstanceIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, changed=False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        existing = _build_instance(display_name="test-instance")

        module_args.update({
            "instance_id": "ocid1.instance.oc1.phx.test1",
            "display_name": "test-instance",
            "compartment_id": None,
            "availability_domain": None,
            "shape": None,
            "image_id": None,
            "subnet_id": None,
            "shape_config": None,
            "metadata": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        oci_inst = OciInstance(module)

        assert not oci_inst.needs_update(existing)

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_change_needed_when_display_name_differs(self, mock_create_client, module_args):
        """When display_name differs from desired, needs_update returns True."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        existing = _build_instance(display_name="old-name")

        module_args.update({
            "instance_id": "ocid1.instance.oc1.phx.test1",
            "display_name": "new-name",
            "compartment_id": None,
            "availability_domain": None,
            "shape": None,
            "image_id": None,
            "subnet_id": None,
            "shape_config": None,
            "metadata": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_instance import OciInstance
        oci_inst = OciInstance(module)

        assert oci_inst.needs_update(existing)
