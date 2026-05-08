"""Unit tests for oracle.oci.oci_compartment module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_compartment"


def _build_compartment(
    compartment_id="ocid1.compartment.oc1..test1",
    name="test-compartment",
    description="Test compartment for unit tests",
    lifecycle_state="ACTIVE",
    parent_compartment_id="ocid1.tenancy.oc1..testtenancy",
):
    """Return a mock OCI compartment object."""
    compartment = MagicMock()
    compartment.id = compartment_id
    compartment.name = name
    compartment.description = description
    compartment.lifecycle_state = lifecycle_state
    compartment.compartment_id = parent_compartment_id
    compartment.freeform_tags = {}
    compartment.defined_tags = {}
    return compartment


@pytest.fixture
def compartment_create_args(module_args):
    """Module args for creating a compartment."""
    module_args.update({
        "parent_compartment_id": "ocid1.tenancy.oc1..testtenancy",
        "name": "test-compartment",
        "description": "Test compartment for unit tests",
        "compartment_id": None,
    })
    return module_args


class TestOciCompartmentCreate:
    """Test compartment creation (uses standalone functions, not OciResourceBase)."""

    @patch(f"{MODULE_PATH}.wait_for_resource")
    @patch(f"{MODULE_PATH}.call_with_retry")
    def test_create_compartment(self, mock_call_retry, mock_wait, compartment_create_args):
        """Creating a compartment calls create_compartment and waits for ACTIVE."""
        mock_client = MagicMock()

        creating = _build_compartment(lifecycle_state="CREATING")
        mock_response = MagicMock()
        mock_response.data = creating
        mock_call_retry.return_value = mock_response

        active = _build_compartment(lifecycle_state="ACTIVE")
        mock_wait.return_value = active

        module = MagicMock()
        module.params = compartment_create_args

        from ansible_collections.oracle.oci.plugins.modules.oci_compartment import create_resource
        result = create_resource(mock_client, module)

        mock_call_retry.assert_called_once()
        assert mock_call_retry.call_args[0][0] == mock_client.create_compartment
        create_details = mock_call_retry.call_args[0][1]
        assert create_details.compartment_id == "ocid1.tenancy.oc1..testtenancy"
        assert create_details.name == "test-compartment"
        assert result.lifecycle_state == "ACTIVE"

    @patch(f"{MODULE_PATH}.wait_for_resource")
    @patch(f"{MODULE_PATH}.call_with_retry")
    def test_create_compartment_with_description(self, mock_call_retry, mock_wait, compartment_create_args):
        """Description is passed through to CreateCompartmentDetails."""
        mock_client = MagicMock()
        compartment_create_args["description"] = "Custom description"

        mock_response = MagicMock()
        mock_response.data = _build_compartment(lifecycle_state="CREATING")
        mock_call_retry.return_value = mock_response
        mock_wait.return_value = _build_compartment(description="Custom description")

        module = MagicMock()
        module.params = compartment_create_args

        from ansible_collections.oracle.oci.plugins.modules.oci_compartment import create_resource
        create_resource(mock_client, module)

        create_details = mock_call_retry.call_args[0][1]
        assert create_details.description == "Custom description"


class TestOciCompartmentDelete:
    """Test compartment deletion."""

    @patch(f"{MODULE_PATH}.wait_for_resource")
    @patch(f"{MODULE_PATH}.call_with_retry")
    def test_delete_compartment(self, mock_call_retry, mock_wait, module_args):
        """Deleting a compartment calls delete_compartment with resource id."""
        mock_client = MagicMock()
        resource = _build_compartment()

        module = MagicMock()
        module.params = module_args

        from ansible_collections.oracle.oci.plugins.modules.oci_compartment import delete_resource
        delete_resource(mock_client, module, resource)

        mock_call_retry.assert_called_once()
        assert mock_call_retry.call_args[0][0] == mock_client.delete_compartment
        assert mock_call_retry.call_args[0][1] == resource.id

    def test_delete_compartment_already_gone(self, module_args):
        """When compartment does not exist, get_compartment raises 404."""
        mock_client = MagicMock()

        import oci.exceptions
        mock_client.get_compartment.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        with pytest.raises(oci.exceptions.ServiceError) as exc_info:
            mock_client.get_compartment("ocid1.compartment.oc1..doesnotexist")
        assert exc_info.value.status == 404


class TestOciCompartmentUpdate:
    """Test compartment update."""

    @patch(f"{MODULE_PATH}.wait_for_resource")
    @patch(f"{MODULE_PATH}.call_with_retry")
    def test_update_name(self, mock_call_retry, mock_wait, module_args):
        """Updating name calls update_compartment."""
        mock_client = MagicMock()

        module_args.update({
            "compartment_id": "ocid1.compartment.oc1..test1",
            "name": "renamed-compartment",
            "description": None,
            "freeform_tags": None,
            "defined_tags": None,
        })

        updated = _build_compartment(name="renamed-compartment")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_call_retry.return_value = mock_response
        mock_wait.return_value = updated

        module = MagicMock()
        module.params = module_args

        resource = _build_compartment(name="old-name")

        from ansible_collections.oracle.oci.plugins.modules.oci_compartment import update_resource
        result = update_resource(mock_client, module, resource)

        mock_call_retry.assert_called_once()
        assert mock_call_retry.call_args[0][0] == mock_client.update_compartment
        assert mock_call_retry.call_args[0][1] == resource.id


class TestOciCompartmentIdempotent:
    """Test idempotent behavior when no change is needed."""

    def test_no_change_needed(self, module_args):
        """When current state matches desired state, needs_update returns False."""
        module_args.update({
            "name": "test-compartment",
            "description": "Test compartment for unit tests",
            "freeform_tags": None,
            "defined_tags": None,
        })

        module = MagicMock()
        module.params = module_args

        resource = _build_compartment(name="test-compartment", description="Test compartment for unit tests")

        from ansible_collections.oracle.oci.plugins.modules.oci_compartment import needs_update
        assert not needs_update(module, resource)

    def test_change_needed_when_name_differs(self, module_args):
        """When name differs from desired, needs_update returns True."""
        module_args.update({
            "name": "new-name",
            "description": None,
            "freeform_tags": None,
            "defined_tags": None,
        })

        module = MagicMock()
        module.params = module_args

        resource = _build_compartment(name="old-name")

        from ansible_collections.oracle.oci.plugins.modules.oci_compartment import needs_update
        assert needs_update(module, resource)
