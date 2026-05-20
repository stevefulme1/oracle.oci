"""Unit tests for oracle.oci.oci_notification_topic module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_notification_topic"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_topic(
    name="test-topic",
    description="Test notification topic",
):
    """Return a mock OCI notification topic object."""
    topic = MagicMock()
    topic.name = name
    topic.description = description
    topic.topic_id = "ocid1.onstopic.oc1..testresource"
    topic.compartment_id = "ocid1.compartment.oc1..test"
    topic.lifecycle_state = "ACTIVE"
    topic.freeform_tags = {}
    topic.defined_tags = {}
    return topic


@pytest.fixture
def topic_create_args(module_args):
    """Module args for creating a topic."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "name": "test-topic",
        "description": "Test notification topic",
        "topic_id": None,
    })
    return module_args


class TestOciNotificationTopicCreate:
    """Test topic creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_topic(self, mock_create_client, topic_create_args):
        """Creating a topic calls create_topic."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_topic()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_topic.return_value = mock_response

        module = MagicMock()
        module.params = topic_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_notification_topic import create_topic
        result = create_topic(module, mock_client)

        mock_client.create_topic.assert_called_once()


class TestOciNotificationTopicDelete:
    """Test topic deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_topic(self, mock_create_client, module_args):
        """Deleting a topic calls delete_topic."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "absent",
            "topic_id": "ocid1.onstopic.oc1..testresource",
            "compartment_id": None,
            "name": None,
            "description": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_topic()

        from ansible_collections.oracle.oci.plugins.modules.oci_notification_topic import delete_topic
        delete_topic(module, mock_client, resource)

        mock_client.delete_topic.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_topic_already_gone(self, mock_create_client, module_args):
        """When topic does not exist, get_topic returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_topic.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        from ansible_collections.oracle.oci.plugins.modules.oci_notification_topic import get_topic
        result = get_topic(mock_client, "ocid1.onstopic.oc1..nonexistent")
        assert result is None


class TestOciNotificationTopicUpdate:
    """Test topic update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_topic(self, mock_create_client, module_args):
        """Updating a topic calls update_topic."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "present",
            "name": "updated-topic",
            "description": "Updated description",
            "topic_id": "ocid1.onstopic.oc1..testresource",
            "compartment_id": None,
        })

        updated = _build_topic(name="updated-topic", description="Updated description")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_topic.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_topic()

        from ansible_collections.oracle.oci.plugins.modules.oci_notification_topic import update_topic
        result = update_topic(module, mock_client, resource)

        mock_client.update_topic.assert_called_once()


class TestOciNotificationTopicIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": "test-topic",
            "description": "Test notification topic",
            "topic_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_topic()

        from ansible_collections.oracle.oci.plugins.modules.oci_notification_topic import needs_update
        assert not needs_update(module, resource)
