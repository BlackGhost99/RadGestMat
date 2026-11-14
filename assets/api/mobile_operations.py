"""Internal sync primitives; not yet exposed as a public write endpoint."""
import hashlib
import json
from uuid import UUID

from django.db import transaction
from assets.models import MobileOperationReceipt


class OperationConflict(Exception):
    """An operation ID was reused with different content."""


def execute_once(*, user, operation_id, payload, authorize, mutate):
    """Run authorization on every attempt, including replays.

    mutate must return a JSON-compatible dict and perform only transactional
    database effects. External effects need a separate transactional outbox.
    authorize must raise on revoked access. Receipts must not be pruned while
    clients can still retry old operation IDs.
    """
    operation_id = UUID(str(operation_id))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    fingerprint = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    with transaction.atomic():
        authorize(user, payload)
        receipt, created = MobileOperationReceipt.objects.get_or_create(
            user=user, operation_id=operation_id,
            defaults={"request_hash": fingerprint},
        )
        if not created:
            if receipt.request_hash != fingerprint:
                raise OperationConflict("Operation ID reused with different content")
            return receipt.result
        result = mutate()
        if not isinstance(result, dict):
            raise TypeError("Mutation result must be a JSON object")
        receipt.result = result
        receipt.save(update_fields=["result"])
        return result
