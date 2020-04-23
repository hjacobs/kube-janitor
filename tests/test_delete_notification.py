import datetime
import unittest

from pykube import Namespace
from pykube.utils import obj_merge

from kube_janitor.janitor import add_notification_flag
from kube_janitor.janitor import get_delete_notification_time
from kube_janitor.janitor import handle_resource_on_expiry
from kube_janitor.janitor import handle_resource_on_ttl
from kube_janitor.janitor import was_notified


class MockedNamespace(Namespace):
    def update(self):
        print("Mocked update")
        self.obj = obj_merge(self.obj, self._original_obj)


class TestDeleteNotification(unittest.TestCase):
    def setUp(self):
        self.mocked_resource = MockedNamespace(
            None,
            {
                "metadata": {
                    "annotations": {},
                    "name": "mocked-namespace",
                    "creationTimestamp": "2019-03-11T11:10:09Z",
                }
            },
        )

    def test_add_notification_flag(self):
        add_notification_flag(self.mocked_resource, dry_run=False)
        self.assertEqual(
            self.mocked_resource.obj.get("metadata")
            .get("annotations")
            .get("janitor/notified"),
            "yes",
        )

    def test_add_notification_flag_dry_run(self):
        add_notification_flag(self.mocked_resource, dry_run=True)
        self.assertIsNone(
            self.mocked_resource.obj.get("metadata")
            .get("annotations")
            .get("janitor/notified", None)
        )

    def test_was_notified(self):
        add_notification_flag(self.mocked_resource, dry_run=False)
        self.assertTrue(was_notified(self.mocked_resource))

    def test_get_delete_notification(self):
        expire = datetime.datetime.strptime(
            "2019-03-11T11:15:09Z", "%Y-%m-%dT%H:%M:%SZ"
        )
        expected_notification_datetime = datetime.datetime.strptime(
            "2019-03-11T11:10:09Z", "%Y-%m-%dT%H:%M:%SZ"
        )
        delete_notification = 300  # 5 minutes
        self.assertEqual(
            get_delete_notification_time(expire, delete_notification),
            expected_notification_datetime,
        )

    @unittest.mock.patch(
        "kube_janitor.janitor.utcnow",
        return_value=datetime.datetime.strptime(
            "2019-03-11T11:10:09Z", "%Y-%m-%dT%H:%M:%SZ"
        ),
    )
    @unittest.mock.patch("kube_janitor.janitor.add_notification_flag")
    def test_handle_resource_ttl_annotation_with_notification_not_triggered(
        self, mocked_add_notification_flag, mocked_utcnow
    ):
        # Resource was created: 2019-03-11T11:05:00Z
        # ttl is 10 minutes, so it will expire: 2019-03-11T11:15:00Z
        # Current datetime is: 2019-03-11T11:10:09Z
        # Notification is 3 minutes: 180s. Has to notify after: 2019-03-11T11:12:00Z
        resource = Namespace(
            None,
            {
                "metadata": {
                    "name": "foo",
                    "annotations": {"janitor/ttl": "10m"},
                    "creationTimestamp": "2019-03-11T11:05:00Z",
                }
            },
        )
        delete_notification = 180
        handle_resource_on_ttl(
            resource,
            [],
            delete_notification,
            deployment_time_annotation=None,
            dry_run=True,
        )
        mocked_add_notification_flag.assert_not_called()

    @unittest.mock.patch(
        "kube_janitor.janitor.utcnow",
        return_value=datetime.datetime.strptime(
            "2019-03-11T11:13:09Z", "%Y-%m-%dT%H:%M:%SZ"
        ),
    )
    @unittest.mock.patch("kube_janitor.janitor.add_notification_flag")
    def test_handle_resource_ttl_annotation_with_notification_triggered(
        self, mocked_add_notification_flag, mocked_utcnow
    ):
        # Resource was created: 2019-03-11T11:05:00Z
        # ttl is 10 minutes, so it will expire: 2019-03-11T11:15:00Z
        # Current datetime is: 2019-03-11T11:13:09Z
        # Notification is 3 minutes: 180s. Has to notify after: 2019-03-11T11:12:00Z
        resource = Namespace(
            None,
            {
                "metadata": {
                    "name": "foo",
                    "annotations": {"janitor/ttl": "10m"},
                    "creationTimestamp": "2019-03-11T11:05:00Z",
                }
            },
        )
        delete_notification = 180
        handle_resource_on_ttl(
            resource,
            [],
            delete_notification,
            deployment_time_annotation=None,
            dry_run=True,
        )
        mocked_add_notification_flag.assert_called()

    @unittest.mock.patch(
        "kube_janitor.janitor.utcnow",
        return_value=datetime.datetime.strptime(
            "2019-03-11T11:13:09Z", "%Y-%m-%dT%H:%M:%SZ"
        ),
    )
    @unittest.mock.patch("kube_janitor.janitor.add_notification_flag")
    def test_handle_resource_ttl_annotation_with_forever_value_not_triggered(
        self, mocked_add_notification_flag, mocked_utcnow
    ):
        # Resource was created: 2019-03-11T11:05:00Z
        # ttl is `forever`, so it will not expire
        # Current datetime is: 2019-03-11T11:13:09Z
        # Notification is 3 minutes: 180s. Has to notify after: 2019-03-11T11:12:00Z
        resource = Namespace(
            None,
            {
                "metadata": {
                    "name": "foo",
                    "annotations": {"janitor/ttl": "forever"},
                    "creationTimestamp": "2019-03-11T11:05:00Z",
                }
            },
        )
        delete_notification = 180
        counter = handle_resource_on_ttl(
            resource,
            [],
            delete_notification,
            deployment_time_annotation=None,
            dry_run=True,
        )
        self.assertEqual(1, counter["resources-processed"])
        self.assertEqual(1, len(counter))
        mocked_add_notification_flag.assert_not_called()

    @unittest.mock.patch(
        "kube_janitor.janitor.utcnow",
        return_value=datetime.datetime.strptime(
            "2019-03-11T11:13:09Z", "%Y-%m-%dT%H:%M:%SZ"
        ),
    )
    @unittest.mock.patch("kube_janitor.janitor.create_event")
    def test_handle_resource_ttl_annotation_notification_event(
        self, mocked_create_event, mocked_utcnow
    ):
        # Resource was created: 2019-03-11T11:05:00Z
        # ttl is 10 minutes, so it will expire: 2019-03-11T11:15:00Z
        # Current datetime is: 2019-03-11T11:13:09Z
        # Notification is 3 minutes: 180s. Has to notify after: 2019-03-11T11:12:00Z
        resource = MockedNamespace(
            None,
            {
                "metadata": {
                    "name": "foo",
                    "annotations": {"janitor/ttl": "10m"},
                    "creationTimestamp": "2019-03-11T11:05:00Z",
                }
            },
        )
        delete_notification = 180
        handle_resource_on_ttl(
            resource,
            [],
            delete_notification,
            deployment_time_annotation=None,
            dry_run=True,
        )
        expire = datetime.datetime.strptime(
            "2019-03-11T11:15:00Z", "%Y-%m-%dT%H:%M:%SZ"
        )
        formatted_expire_datetime = expire.strftime("%Y-%m-%dT%H:%M:%SZ")
        reason = "annotation janitor/ttl is set"
        message = f"{resource.kind} {resource.name} will be deleted at {formatted_expire_datetime} ({reason})"
        mocked_create_event.assert_called_with(
            resource, message, "DeleteNotification", dry_run=True
        )

    @unittest.mock.patch(
        "kube_janitor.janitor.utcnow",
        return_value=datetime.datetime.strptime(
            "2019-03-11T11:13:09Z", "%Y-%m-%dT%H:%M:%SZ"
        ),
    )
    @unittest.mock.patch("kube_janitor.janitor.create_event")
    def test_handle_resource_ttl_annotation_notification_deployment_time_event(
        self, mocked_create_event, mocked_utcnow
    ):
        # Resource was created at 2019-03-01T00:00:00Z and redeployed at 2019-03-11T11:05:00Z
        # ttl is 10 minutes, so it will expire: 2019-03-11T11:15:00Z
        # Current datetime is: 2019-03-11T11:13:09Z
        # Notification is 3 minutes: 180s. Has to notify after: 2019-03-11T11:12:00Z
        resource = MockedNamespace(
            None,
            {
                "metadata": {
                    "name": "foo",
                    "annotations": {
                        "janitor/ttl": "10m",
                        "deploymentTime": "2019-03-11T11:05:00Z",
                    },
                    "creationTimestamp": "2019-03-01T00:00:00Z",
                }
            },
        )
        delete_notification = 180
        handle_resource_on_ttl(
            resource,
            [],
            delete_notification,
            deployment_time_annotation="deploymentTime",
            dry_run=True,
        )
        expire = datetime.datetime.strptime(
            "2019-03-11T11:15:00Z", "%Y-%m-%dT%H:%M:%SZ"
        )
        formatted_expire_datetime = expire.strftime("%Y-%m-%dT%H:%M:%SZ")
        reason = "annotation janitor/ttl is set"
        message = f"{resource.kind} {resource.name} will be deleted at {formatted_expire_datetime} ({reason})"
        mocked_create_event.assert_called_with(
            resource, message, "DeleteNotification", dry_run=True
        )

    @unittest.mock.patch(
        "kube_janitor.janitor.utcnow",
        return_value=datetime.datetime.strptime(
            "2019-03-11T11:10:09Z", "%Y-%m-%dT%H:%M:%SZ"
        ),
    )
    @unittest.mock.patch("kube_janitor.janitor.add_notification_flag")
    def test_handle_resource_expiry_annotation_with_notification_not_triggered(
        self, mocked_add_notification_flag, mocked_utcnow
    ):
        # Resource was created: 2019-03-11T11:05:00Z
        # Expire is set to: 2019-03-11T11:15:00Z
        # Current datetime is: 2019-03-11T11:10:09Z
        # Notification is 3 minutes: 180s. Has to notify after: 2019-03-11T11:12:00Z
        resource = Namespace(
            None,
            {
                "metadata": {
                    "name": "foo",
                    "annotations": {"janitor/expires": "2019-03-11T11:15:00Z"},
                    "creationTimestamp": "2019-03-11T11:05:00Z",
                }
            },
        )
        delete_notification = 180
        handle_resource_on_expiry(
            resource, [], delete_notification, wait_after_delete=0, dry_run=True
        )
        mocked_add_notification_flag.assert_not_called()

    @unittest.mock.patch(
        "kube_janitor.janitor.utcnow",
        return_value=datetime.datetime.strptime(
            "2019-03-11T11:12:09Z", "%Y-%m-%dT%H:%M:%SZ"
        ),
    )
    @unittest.mock.patch("kube_janitor.janitor.add_notification_flag")
    def test_handle_resource_expiry_annotation_with_notification_triggered(
        self, mocked_add_notification_flag, mocked_utcnow
    ):
        # Resource was created: 2019-03-11T11:05:00Z
        # Expire is set to: 2019-03-11T11:15:00Z
        # Current datetime is: 2019-03-11T11:10:09Z
        # Notification is 3 minutes: 180s. Has to notify after: 2019-03-11T11:12:00Z
        resource = Namespace(
            None,
            {
                "metadata": {
                    "name": "foo",
                    "annotations": {"janitor/expires": "2019-03-11T11:15:00Z"},
                    "creationTimestamp": "2019-03-11T11:05:00Z",
                }
            },
        )
        delete_notification = 180
        handle_resource_on_expiry(
            resource, [], delete_notification, wait_after_delete=0, dry_run=True
        )
        mocked_add_notification_flag.assert_called()

    @unittest.mock.patch(
        "kube_janitor.janitor.utcnow",
        return_value=datetime.datetime.strptime(
            "2019-03-11T11:12:09Z", "%Y-%m-%dT%H:%M:%SZ"
        ),
    )
    @unittest.mock.patch("kube_janitor.janitor.create_event")
    def test_handle_resource_expiry_annotation_notification_event(
        self, mocked_create_event, mocked_utcnow
    ):
        # Resource was created: 2019-03-11T11:05:00Z
        # Expire is set to: 2019-03-11T11:15:00Z
        # Current datetime is: 2019-03-11T11:10:09Z
        # Notification is 3 minutes: 180s. Has to notify after: 2019-03-11T11:12:00Z
        resource = MockedNamespace(
            None,
            {
                "metadata": {
                    "name": "foo",
                    "annotations": {"janitor/expires": "2019-03-11T11:15:00Z"},
                    "creationTimestamp": "2019-03-11T11:05:00Z",
                }
            },
        )
        delete_notification = 180
        handle_resource_on_expiry(
            resource, [], delete_notification, wait_after_delete=0, dry_run=True
        )

        expire = datetime.datetime.strptime(
            "2019-03-11T11:15:00Z", "%Y-%m-%dT%H:%M:%SZ"
        )
        formatted_expire_datetime = expire.strftime("%Y-%m-%dT%H:%M:%SZ")
        reason = "annotation janitor/expires is set"
        message = f"{resource.kind} {resource.name} will be deleted at {formatted_expire_datetime} ({reason})"
        mocked_create_event.assert_called_with(
            resource, message, "DeleteNotification", dry_run=True
        )
