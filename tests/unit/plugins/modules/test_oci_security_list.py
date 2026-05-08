"""Unit tests for oracle.oci.oci_security_list module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_security_list"
AUTH_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_wait"


def _build_security_list(
    security_list_id="ocid1.securitylist.oc1..test1",
    display_name="test-security-list",
    lifecycle_state="AVAILABLE",
    vcn_id="ocid1.vcn.oc1..test1",
    compartment_id="ocid1.compartment.oc1..test",
    ingress_security_rules=None,
    egress_security_rules=None,
):
    """Return a mock OCI security list object."""
    sl = MagicMock()
    sl.id = security_list_id
    sl.display_name = display_name
    sl.lifecycle_state = lifecycle_state
    sl.vcn_id = vcn_id
    sl.compartment_id = compartment_id
    sl.ingress_security_rules = ingress_security_rules or []
    sl.egress_security_rules = egress_security_rules or []
    sl.freeform_tags = {}
    sl.defined_tags = {}
    return sl


@pytest.fixture
def security_list_create_args(module_args):
    """Module args for creating a security list."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "vcn_id": "ocid1.vcn.oc1..test1",
        "display_name": "test-security-list",
        "ingress_security_rules": [
            {
                "protocol": "6",
                "source": "0.0.0.0/0",
                "tcp_options": {"destination_port_range": {"min": 22, "max": 22}},
            },
        ],
        "egress_security_rules": [
            {
                "protocol": "all",
                "destination": "0.0.0.0/0",
            },
        ],
        "security_list_id": None,
    })
    return module_args


class TestOciSecurityListCreate:
    """Test security list creation."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_security_list(self, mock_create_client, mock_wait, security_list_create_args):
        """Creating a security list calls create_security_list and waits for AVAILABLE."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        provisioning_sl = _build_security_list(lifecycle_state="PROVISIONING")
        mock_response = MagicMock()
        mock_response.data = provisioning_sl
        mock_client.create_security_list.return_value = mock_response

        available_sl = _build_security_list(lifecycle_state="AVAILABLE")
        mock_wait.return_value = available_sl

        module = MagicMock()
        module.params = security_list_create_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list import OciSecurityList
        oci_sl = OciSecurityList(module)
        result = oci_sl.create_resource()

        mock_client.create_security_list.assert_called_once()
        create_details = mock_client.create_security_list.call_args[0][0]
        assert create_details.compartment_id == "ocid1.compartment.oc1..test"
        assert create_details.vcn_id == "ocid1.vcn.oc1..test1"
        assert create_details.display_name == "test-security-list"
        assert result.lifecycle_state == "AVAILABLE"

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_security_list_with_rules(self, mock_create_client, mock_wait, security_list_create_args):
        """Ingress and egress rules are passed through to create details."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.data = _build_security_list(lifecycle_state="PROVISIONING")
        mock_client.create_security_list.return_value = mock_response
        mock_wait.return_value = _build_security_list()

        module = MagicMock()
        module.params = security_list_create_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list import OciSecurityList
        oci_sl = OciSecurityList(module)
        oci_sl.create_resource()

        create_details = mock_client.create_security_list.call_args[0][0]
        assert create_details.ingress_security_rules is not None
        assert len(create_details.ingress_security_rules) == 1
        assert create_details.egress_security_rules is not None
        assert len(create_details.egress_security_rules) == 1


class TestOciSecurityListDelete:
    """Test security list deletion."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_security_list(self, mock_create_client, mock_wait, module_args):
        """Deleting a security list calls delete_security_list."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "security_list_id": "ocid1.securitylist.oc1..test1",
            "state": "absent",
            "compartment_id": None,
            "vcn_id": None,
            "display_name": None,
            "ingress_security_rules": None,
            "egress_security_rules": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list import OciSecurityList
        resource = _build_security_list()

        oci_sl = OciSecurityList(module)
        oci_sl.delete_resource(resource)

        mock_client.delete_security_list.assert_called_once_with(resource.id)

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_security_list_already_gone(self, mock_create_client, module_args):
        """When security list does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_security_list.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        module_args.update({
            "security_list_id": "ocid1.securitylist.oc1..doesnotexist",
            "state": "absent",
            "compartment_id": None,
            "vcn_id": None,
            "display_name": None,
            "ingress_security_rules": None,
            "egress_security_rules": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list import OciSecurityList
        oci_sl = OciSecurityList(module)
        result = oci_sl.get_resource()
        assert result is None


class TestOciSecurityListUpdate:
    """Test security list update."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_display_name(self, mock_create_client, mock_wait, module_args):
        """Updating display_name calls update_security_list."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "security_list_id": "ocid1.securitylist.oc1..test1",
            "display_name": "renamed-security-list",
            "compartment_id": None,
            "vcn_id": None,
            "ingress_security_rules": None,
            "egress_security_rules": None,
        })

        updated_sl = _build_security_list(display_name="renamed-security-list")
        mock_wait.return_value = updated_sl

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list import OciSecurityList
        resource = _build_security_list(display_name="old-name")

        oci_sl = OciSecurityList(module)
        result = oci_sl.update_resource(resource)

        mock_client.update_security_list.assert_called_once()
        assert mock_client.update_security_list.call_args[0][0] == resource.id
        assert result.display_name == "renamed-security-list"


class TestOciSecurityListIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "security_list_id": "ocid1.securitylist.oc1..test1",
            "display_name": "test-security-list",
            "compartment_id": None,
            "vcn_id": None,
            "ingress_security_rules": None,
            "egress_security_rules": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list import OciSecurityList
        resource = _build_security_list(display_name="test-security-list")

        oci_sl = OciSecurityList(module)
        assert not oci_sl.needs_update(resource)

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_change_needed_when_display_name_differs(self, mock_create_client, module_args):
        """When display_name differs from desired, needs_update returns True."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "security_list_id": "ocid1.securitylist.oc1..test1",
            "display_name": "new-name",
            "compartment_id": None,
            "vcn_id": None,
            "ingress_security_rules": None,
            "egress_security_rules": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list import OciSecurityList
        resource = _build_security_list(display_name="old-name")

        oci_sl = OciSecurityList(module)
        assert oci_sl.needs_update(resource)
