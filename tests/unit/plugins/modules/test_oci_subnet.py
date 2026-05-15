"""Unit tests for stevefulme1.oci_cloud.oci_subnet module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_subnet"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_subnet(
    subnet_id="ocid1.subnet.oc1.phx.test1",
    display_name="test-subnet",
    lifecycle_state="AVAILABLE",
    cidr_block="10.0.1.0/24",
    vcn_id="ocid1.vcn.oc1..test1",
    compartment_id="ocid1.compartment.oc1..test",
    availability_domain="Uocm:PHX-AD-1",
    dns_label="testsub",
):
    """Return a mock OCI subnet object."""
    subnet = MagicMock()
    subnet.id = subnet_id
    subnet.display_name = display_name
    subnet.lifecycle_state = lifecycle_state
    subnet.cidr_block = cidr_block
    subnet.vcn_id = vcn_id
    subnet.compartment_id = compartment_id
    subnet.availability_domain = availability_domain
    subnet.dns_label = dns_label
    subnet.freeform_tags = {}
    subnet.defined_tags = {}
    return subnet


@pytest.fixture
def subnet_create_args(module_args):
    """Module args for creating a subnet."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "vcn_id": "ocid1.vcn.oc1..test1",
        "cidr_block": "10.0.1.0/24",
        "display_name": "test-subnet",
        "dns_label": "testsub",
        "availability_domain": "Uocm:PHX-AD-1",
        "subnet_id": None,
    })
    return module_args


class TestOciSubnetCreate:
    """Test subnet creation."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_subnet(self, mock_create_client, mock_wait, subnet_create_args):
        """Creating a subnet calls create_subnet and waits for AVAILABLE."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        provisioning_subnet = _build_subnet(lifecycle_state="PROVISIONING")
        mock_response = MagicMock()
        mock_response.data = provisioning_subnet
        mock_client.create_subnet.return_value = mock_response

        available_subnet = _build_subnet(lifecycle_state="AVAILABLE")
        mock_wait.return_value = available_subnet

        module = MagicMock()
        module.params = subnet_create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_subnet import OciSubnet
        oci_subnet = OciSubnet(module)
        result = oci_subnet.create_resource()

        mock_client.create_subnet.assert_called_once()
        create_details = mock_client.create_subnet.call_args[0][0]
        assert create_details.compartment_id == "ocid1.compartment.oc1..test"
        assert create_details.vcn_id == "ocid1.vcn.oc1..test1"
        assert create_details.cidr_block == "10.0.1.0/24"
        assert create_details.display_name == "test-subnet"
        assert result.lifecycle_state == "AVAILABLE"

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_subnet_with_dns_label(self, mock_create_client, mock_wait, subnet_create_args):
        """DNS label is passed through to CreateSubnetDetails."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.data = _build_subnet(lifecycle_state="PROVISIONING")
        mock_client.create_subnet.return_value = mock_response
        mock_wait.return_value = _build_subnet()

        module = MagicMock()
        module.params = subnet_create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_subnet import OciSubnet
        oci_subnet = OciSubnet(module)
        oci_subnet.create_resource()

        create_details = mock_client.create_subnet.call_args[0][0]
        assert create_details.dns_label == "testsub"


class TestOciSubnetDelete:
    """Test subnet deletion."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_subnet(self, mock_create_client, mock_wait, module_args):
        """Deleting a subnet calls delete_subnet."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "subnet_id": "ocid1.subnet.oc1.phx.test1",
            "state": "absent",
            "compartment_id": None,
            "vcn_id": None,
            "cidr_block": None,
            "display_name": None,
            "dns_label": None,
            "availability_domain": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_subnet import OciSubnet
        resource = _build_subnet()

        oci_subnet = OciSubnet(module)
        oci_subnet.delete_resource(resource)

        mock_client.delete_subnet.assert_called_once_with(resource.id)

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_subnet_already_gone(self, mock_create_client, module_args):
        """When subnet does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_subnet.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        module_args.update({
            "subnet_id": "ocid1.subnet.oc1.phx.doesnotexist",
            "state": "absent",
            "compartment_id": None,
            "vcn_id": None,
            "cidr_block": None,
            "display_name": None,
            "dns_label": None,
            "availability_domain": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_subnet import OciSubnet
        oci_subnet = OciSubnet(module)
        result = oci_subnet.get_resource()
        assert result is None


class TestOciSubnetUpdate:
    """Test subnet update."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_display_name(self, mock_create_client, mock_wait, module_args):
        """Updating display_name calls update_subnet."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "subnet_id": "ocid1.subnet.oc1.phx.test1",
            "display_name": "renamed-subnet",
            "compartment_id": None,
            "vcn_id": None,
            "cidr_block": None,
            "dns_label": None,
            "availability_domain": None,
        })

        updated_subnet = _build_subnet(display_name="renamed-subnet")
        mock_wait.return_value = updated_subnet

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_subnet import OciSubnet
        resource = _build_subnet(display_name="old-name")

        oci_subnet = OciSubnet(module)
        result = oci_subnet.update_resource(resource)

        mock_client.update_subnet.assert_called_once()
        assert mock_client.update_subnet.call_args[0][0] == resource.id
        assert result.display_name == "renamed-subnet"


class TestOciSubnetIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "subnet_id": "ocid1.subnet.oc1.phx.test1",
            "display_name": "test-subnet",
            "compartment_id": None,
            "vcn_id": None,
            "cidr_block": None,
            "dns_label": None,
            "availability_domain": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_subnet import OciSubnet
        resource = _build_subnet(display_name="test-subnet")

        oci_subnet = OciSubnet(module)
        assert not oci_subnet.needs_update(resource)

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_change_needed_when_display_name_differs(self, mock_create_client, module_args):
        """When display_name differs from desired, needs_update returns True."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "subnet_id": "ocid1.subnet.oc1.phx.test1",
            "display_name": "new-name",
            "compartment_id": None,
            "vcn_id": None,
            "cidr_block": None,
            "dns_label": None,
            "availability_domain": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_subnet import OciSubnet
        resource = _build_subnet(display_name="old-name")

        oci_subnet = OciSubnet(module)
        assert oci_subnet.needs_update(resource)
