#!/usr/bin/env python3
"""Create or update a professional invoice template in Resend.

Usage (PowerShell):
  $env:RESEND_API_KEY='re_xxxxx'
  python scripts/create_resend_invoice_template.py

Optional env vars:
  RESEND_INVOICE_TEMPLATE_ALIAS   default: invoice-professional
  RESEND_INVOICE_TEMPLATE_NAME    default: Book Sales Professional Invoice
  SENDER_EMAIL_ADDRESS            optional default sender on template
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

import requests

API_BASE = "https://api.resend.com"


def _require_api_key() -> str:
    key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("RESEND_API_KEY is required")
    return key


def _headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _template_html() -> str:
    return """<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Invoice #{{{ORDER_ID}}}</title>
  </head>
  <body style=\"margin:0;background:#f6f8fb;padding:24px;font-family:Segoe UI,Arial,sans-serif;color:#111827;\">
    <table role=\"presentation\" style=\"width:100%;max-width:720px;margin:0 auto;border-collapse:collapse;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;\">
      <tr>
        <td bgcolor=\"#1f2937\" style=\"padding:24px 28px;background:#1f2937;background:linear-gradient(135deg,#0f172a,#1f2937);color:#ffffff;\">
          <div style=\"font-size:12px;letter-spacing:1px;text-transform:uppercase;opacity:0.85;\">Book Sales Website</div>
          <div style=\"font-size:28px;font-weight:700;margin-top:6px;\">Invoice</div>
          <div style=\"font-size:13px;opacity:0.9;margin-top:6px;\">Pathway: {{{PATHWAY}}}</div>
        </td>
      </tr>
      <tr>
        <td style=\"padding:24px 28px;\">
          <table role=\"presentation\" style=\"width:100%;border-collapse:collapse;\">
            <tr>
              <td style=\"font-size:14px;color:#4b5563;\">Invoice Number</td>
              <td style=\"font-size:14px;color:#111827;font-weight:600;text-align:right;\">#{{{ORDER_ID}}}</td>
            </tr>
            <tr>
              <td style=\"font-size:14px;color:#4b5563;padding-top:6px;\">Date</td>
              <td style=\"font-size:14px;color:#111827;text-align:right;padding-top:6px;\">{{{ORDER_DATE}}}</td>
            </tr>
            <tr>
              <td style=\"font-size:14px;color:#4b5563;padding-top:6px;\">Customer</td>
              <td style=\"font-size:14px;color:#111827;text-align:right;padding-top:6px;\">{{{CUSTOMER_NAME}}} &lt;{{{CUSTOMER_EMAIL}}}&gt;</td>
            </tr>
          </table>

          <div style=\"margin-top:22px;font-size:16px;font-weight:600;color:#111827;\">Order Details</div>
          <table role=\"presentation\" style=\"width:100%;margin-top:10px;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;\">
            <thead>
              <tr style=\"background:#f9fafb;\">
                <th style=\"padding:10px;text-align:left;font-size:13px;color:#374151;border-bottom:1px solid #e5e7eb;\">Item</th>
                <th style=\"padding:10px;text-align:center;font-size:13px;color:#374151;border-bottom:1px solid #e5e7eb;\">Qty</th>
                <th style=\"padding:10px;text-align:right;font-size:13px;color:#374151;border-bottom:1px solid #e5e7eb;\">Price</th>
                <th style=\"padding:10px;text-align:right;font-size:13px;color:#374151;border-bottom:1px solid #e5e7eb;\">Line Total</th>
              </tr>
            </thead>
            <tbody>
              {{{ITEM_ROWS}}}
            </tbody>
          </table>

          <table role=\"presentation\" style=\"width:100%;margin-top:14px;border-collapse:collapse;\">
            <tr>
              <td style=\"font-size:14px;color:#4b5563;\">Total</td>
              <td style=\"text-align:right;font-size:20px;color:#111827;font-weight:700;\">£{{{ORDER_TOTAL}}}</td>
            </tr>
          </table>

          <p style=\"margin-top:20px;font-size:13px;color:#6b7280;line-height:1.5;\">
            Thank you for your purchase. If you have any questions about this invoice,
            reply to this email and our team will help.
          </p>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _template_variables() -> list[Dict[str, Any]]:
    return [
        {"key": "PATHWAY", "type": "string", "fallbackValue": "customer"},
        {"key": "ORDER_ID", "type": "number", "fallbackValue": 0},
        {"key": "ORDER_DATE", "type": "string", "fallbackValue": ""},
        {"key": "CUSTOMER_NAME", "type": "string", "fallbackValue": "Customer"},
        {"key": "CUSTOMER_EMAIL", "type": "string", "fallbackValue": "customer@example.com"},
        {"key": "ITEM_ROWS", "type": "string", "fallbackValue": "<tr><td colspan='4'>No items</td></tr>"},
        {"key": "ORDER_TOTAL", "type": "string", "fallbackValue": "0.00"},
    ]


def _get_existing_template_id(api_key: str, alias: str) -> Optional[str]:
    resp = requests.get(f"{API_BASE}/templates", headers=_headers(api_key), timeout=20)
    if resp.status_code >= 400:
        return None

    data = resp.json().get("data", [])
    for item in data:
        if item.get("alias") == alias:
            return item.get("id")
    return None


def _create_template(api_key: str, payload: Dict[str, Any]) -> str:
    resp = requests.post(f"{API_BASE}/templates", headers=_headers(api_key), json=payload, timeout=20)
    if resp.status_code >= 400:
        raise RuntimeError(f"Create template failed {resp.status_code}: {resp.text}")
    return resp.json().get("id") or resp.json().get("data", {}).get("id")


def _update_template(api_key: str, template_id: str, payload: Dict[str, Any]) -> None:
    resp = requests.patch(f"{API_BASE}/templates/{template_id}", headers=_headers(api_key), json=payload, timeout=20)
    if resp.status_code >= 400:
        raise RuntimeError(f"Update template failed {resp.status_code}: {resp.text}")


def _publish_template(api_key: str, template_id: str) -> None:
    resp = requests.post(f"{API_BASE}/templates/{template_id}/publish", headers=_headers(api_key), timeout=20)
    if resp.status_code >= 400:
        raise RuntimeError(f"Publish template failed {resp.status_code}: {resp.text}")


def main() -> int:
    api_key = _require_api_key()
    alias = (os.environ.get("RESEND_INVOICE_TEMPLATE_ALIAS") or "invoice-professional").strip()
    name = (os.environ.get("RESEND_INVOICE_TEMPLATE_NAME") or "Book Sales Professional Invoice").strip()
    sender = (os.environ.get("SENDER_EMAIL_ADDRESS") or "").strip()

    payload: Dict[str, Any] = {
        "name": name,
        "alias": alias,
        "subject": "Invoice #{{{ORDER_ID}}}",
        "html": _template_html(),
        "variables": _template_variables(),
    }
    if sender:
        payload["from"] = sender

    template_id = _get_existing_template_id(api_key, alias)

    if template_id:
        _update_template(api_key, template_id, payload)
        action = "updated"
    else:
        template_id = _create_template(api_key, payload)
        action = "created"

    if not template_id:
        raise RuntimeError("Template ID not returned by Resend")

    _publish_template(api_key, template_id)

    print(json.dumps({
        "status": "ok",
        "action": action,
        "template_id": template_id,
        "alias": alias,
        "env_to_set": f"RESEND_INVOICE_TEMPLATE_ID={template_id}",
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
