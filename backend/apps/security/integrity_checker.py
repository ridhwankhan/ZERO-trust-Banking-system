"""
Cryptographic Ledger Integrity Checker (Module 3)
=================================================
Walks the full Transaction table in order and re-computes SHA-256
hashes to verify the chain has not been tampered with.

Usage:
    from apps.security.integrity_checker import verify_ledger_integrity
    report = verify_ledger_integrity()
"""

import hashlib
import logging

from django.core.mail import mail_admins

from apps.transactions.models import Transaction
from .models import LedgerIntegrityReport, SecurityAlert

logger = logging.getLogger(__name__)


def _compute_tx_hash(tx, previous_hash):
    """
    Deterministically hash the canonical fields of a transaction.
    Must match the formula used when creating transactions.
    """
    sender_id = str(tx.sender_id) if tx.sender_id else '0'
    receiver_id = str(tx.receiver_id)
    amount = str(tx.amount)
    payload = tx.encrypted_payload or ''
    prev = previous_hash or 'GENESIS'

    raw = f"{sender_id}_{receiver_id}_{amount}_{payload}_{prev}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def verify_ledger_integrity():
    """
    Walk every Transaction ordered by pk, recalculate hashes,
    and compare against stored hashes.

    Returns the created LedgerIntegrityReport.
    """
    transactions = Transaction.objects.all().order_by('id')
    verified = 0
    tampered = []
    previous_hash = None

    for tx in transactions.iterator():
        expected = _compute_tx_hash(tx, previous_hash)

        if tx.transaction_hash and tx.transaction_hash != expected:
            tampered.append({
                'transaction_id': tx.id,
                'expected_hash': expected,
                'actual_hash': tx.transaction_hash,
            })

        # Advance the chain regardless (use what was stored)
        previous_hash = tx.transaction_hash or expected
        verified += 1

    status = (
        LedgerIntegrityReport.STATUS_TAMPERED if tampered
        else LedgerIntegrityReport.STATUS_SECURE
    )

    report = LedgerIntegrityReport.objects.create(
        status=status,
        verified_count=verified,
        tampered_details=tampered,
    )

    if tampered:
        # Create alerts for every tampered record
        for t in tampered:
            SecurityAlert.objects.create(
                alert_type='LEDGER_TAMPERING',
                severity=SecurityAlert.SEVERITY_HIGH,
                message=(
                    f"Transaction #{t['transaction_id']} hash mismatch. "
                    f"Expected {t['expected_hash'][:16]}…, "
                    f"found {t['actual_hash'][:16]}…"
                ),
            )

        # Email notification to admins
        try:
            mail_admins(
                subject='[CRITICAL] Ledger Integrity Breach Detected',
                message=(
                    f"{len(tampered)} tampered transaction(s) found.\n"
                    f"Run integrity check in the admin dashboard for details."
                ),
            )
        except Exception as exc:
            logger.error("Failed to email admins about integrity breach: %s", exc)

        logger.critical(
            "LEDGER INTEGRITY BREACH: %d tampered transactions detected",
            len(tampered),
        )
    else:
        logger.info(
            "Ledger integrity OK – %d transactions verified", verified)

    return report
