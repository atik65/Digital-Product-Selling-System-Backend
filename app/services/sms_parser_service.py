import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedSms:
    provider: str
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    sender_phone: Optional[str] = None
    balance: Optional[float] = None
    is_received_money: bool = False


class SmsParserService:
    @staticmethod
    def parse(sender: str, message: str) -> ParsedSms:
        sender_upper = sender.upper()
        msg = message.strip()

        if "BKASH" in sender_upper or "BKASH" in msg.upper():
            return SmsParserService._parse_bkash(msg)
        elif "NAGAD" in sender_upper or "NAGAD" in msg.upper():
            return SmsParserService._parse_nagad(msg)
        elif (
            "16216" in sender_upper
            or "ROCKET" in sender_upper
            or "DBBL" in sender_upper
        ):
            return SmsParserService._parse_rocket(msg)
        else:
            return SmsParserService._parse_generic(msg)

    @staticmethod
    def _parse_bkash(msg: str) -> ParsedSms:
        # Check if this is incoming money
        is_received = bool(
            re.search(r"(received|payment received)", msg, re.IGNORECASE)
        )

        # TrxID pattern: e.g. "TrxID 9K48X78L9" or "TrxID: 9K48X78L9"
        trx_match = re.search(r"TrxID:?\s*([A-Z0-9_-]+)", msg, re.IGNORECASE)
        trx_id = trx_match.group(1).upper() if trx_match else None

        # Amount pattern: e.g. "Tk 500.00" or "Tk 1,500.00"
        amount_match = re.search(
            r"(?:Tk|BDT)\s*([0-9,]+(?:\.[0-9]{1,2})?)", msg, re.IGNORECASE
        )
        amount = None
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(",", ""))
            except ValueError:
                amount = None

        # Sender Phone pattern: e.g. "from 01711223344"
        phone_match = re.search(r"from\s*(\+?[0-9]{11,14})", msg, re.IGNORECASE)
        phone = phone_match.group(1) if phone_match else None

        # Balance pattern: e.g. "Balance Tk 1,234.00"
        bal_match = re.search(
            r"Balance\s*(?:Tk|BDT)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
            msg,
            re.IGNORECASE,
        )
        balance = None
        if bal_match:
            try:
                balance = float(bal_match.group(1).replace(",", ""))
            except ValueError:
                balance = None

        return ParsedSms(
            provider="BKASH",
            transaction_id=trx_id,
            amount=amount,
            sender_phone=phone,
            balance=balance,
            is_received_money=is_received and bool(trx_id and amount),
        )

    @staticmethod
    def _parse_nagad(msg: str) -> ParsedSms:
        # Nagad usually contains "TxnID:" or "Txn ID:"
        is_received = bool(re.search(r"(received|amount:|cash in)", msg, re.IGNORECASE))

        # TrxID pattern: e.g. "TxnID: 71KJ892K" or "Txn ID: 71KJ892K"
        trx_match = re.search(r"Txn\s*ID:?\s*([A-Z0-9_-]+)", msg, re.IGNORECASE)
        trx_id = trx_match.group(1).upper() if trx_match else None

        # Amount pattern: e.g. "Amount: Tk 500.00" or "Tk 500.00"
        amount_match = re.search(
            r"(?:Amount:?\s*(?:Tk|BDT)?\s*|(?:Tk|BDT)\s*)([0-9,]+(?:\.[0-9]{1,2})?)",
            msg,
            re.IGNORECASE,
        )
        amount = None
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(",", ""))
            except ValueError:
                amount = None

        # Phone pattern: e.g. "Customer: 01711223344" or "from 01711223344"
        phone_match = re.search(
            r"(?:Customer:?|from)\s*(\+?[0-9]{11,14})", msg, re.IGNORECASE
        )
        phone = phone_match.group(1) if phone_match else None

        # Balance pattern: e.g. "Balance: Tk 2,500.00"
        bal_match = re.search(
            r"Balance:?\s*(?:Tk|BDT)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
            msg,
            re.IGNORECASE,
        )
        balance = None
        if bal_match:
            try:
                balance = float(bal_match.group(1).replace(",", ""))
            except ValueError:
                balance = None

        return ParsedSms(
            provider="NAGAD",
            transaction_id=trx_id,
            amount=amount,
            sender_phone=phone,
            balance=balance,
            is_received_money=is_received and bool(trx_id and amount),
        )

    @staticmethod
    def _parse_rocket(msg: str) -> ParsedSms:
        is_received = bool(re.search(r"(received|credited)", msg, re.IGNORECASE))

        trx_match = re.search(
            r"(?:TxnId|Txn ID|TrxID):?\s*([A-Z0-9_-]+)", msg, re.IGNORECASE
        )
        trx_id = trx_match.group(1).upper() if trx_match else None

        amount_match = re.search(
            r"(?:Tk|BDT)\s*([0-9,]+(?:\.[0-9]{1,2})?)", msg, re.IGNORECASE
        )
        amount = None
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(",", ""))
            except ValueError:
                amount = None

        phone_match = re.search(r"from\s*(\+?[0-9]{11,14})", msg, re.IGNORECASE)
        phone = phone_match.group(1) if phone_match else None

        bal_match = re.search(
            r"Balance:?\s*(?:Tk|BDT)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
            msg,
            re.IGNORECASE,
        )
        balance = None
        if bal_match:
            try:
                balance = float(bal_match.group(1).replace(",", ""))
            except ValueError:
                balance = None

        return ParsedSms(
            provider="ROCKET",
            transaction_id=trx_id,
            amount=amount,
            sender_phone=phone,
            balance=balance,
            is_received_money=is_received and bool(trx_id and amount),
        )

    @staticmethod
    def _parse_generic(msg: str) -> ParsedSms:
        # Fallback parser for any other financial provider
        trx_match = re.search(
            r"(?:TrxID|TxnID|Txn ID|Ref):?\s*([A-Z0-9]{6,})", msg, re.IGNORECASE
        )
        trx_id = trx_match.group(1).upper() if trx_match else None

        amount_match = re.search(
            r"(?:Tk|BDT)\s*([0-9,]+(?:\.[0-9]{1,2})?)", msg, re.IGNORECASE
        )
        amount = None
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(",", ""))
            except ValueError:
                amount = None

        phone_match = re.search(
            r"(?:from|sender):?\s*(\+?[0-9]{11,14})", msg, re.IGNORECASE
        )
        phone = phone_match.group(1) if phone_match else None

        return ParsedSms(
            provider="UNKNOWN",
            transaction_id=trx_id,
            amount=amount,
            sender_phone=phone,
            is_received_money=bool(trx_id and amount),
        )
