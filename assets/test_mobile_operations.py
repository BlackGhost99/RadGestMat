from uuid import uuid4
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from assets.api.mobile_operations import execute_once, OperationConflict
from assets.models import MobileOperationReceipt, Departement


class MobileOperationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="mobile")
        self.operation_id = uuid4()
        self.payload = {"name": "PC"}
        self.calls = 0

    def run_operation(self, payload=None, authorize=lambda user, payload: None, mutate=None):
        def default_mutation():
            self.calls += 1
            return {"id": 123}
        return execute_once(user=self.user, operation_id=self.operation_id,
                            payload=self.payload if payload is None else payload,
                            authorize=authorize, mutate=mutate or default_mutation)

    def test_replay(self):
        self.assertEqual(self.run_operation(), self.run_operation())
        self.assertEqual(self.calls, 1)

    def test_conflicting_payload(self):
        self.run_operation()
        with self.assertRaises(OperationConflict):
            self.run_operation({"name": "Printer"})

    def test_revocation_on_replay(self):
        self.run_operation()
        def deny(user, payload):
            raise PermissionDenied()
        with self.assertRaises(PermissionDenied):
            self.run_operation(authorize=deny)

    def test_rollback(self):
        def fail():
            Departement.objects.create(nom="Rollback", code="RB")
            raise ValueError("failure")
        with self.assertRaises(ValueError):
            self.run_operation(mutate=fail)
        self.assertFalse(MobileOperationReceipt.objects.exists())
        self.assertFalse(Departement.objects.filter(code="RB").exists())
        self.assertEqual(self.run_operation(), {"id": 123})
