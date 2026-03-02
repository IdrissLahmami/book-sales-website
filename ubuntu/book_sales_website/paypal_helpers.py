"""
PayPal Integration Helper Module

This module provides helper functions for PayPal payment processing.
"""

import os
import paypalrestsdk
from flask import url_for, session
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure PayPal
paypalrestsdk.configure({
    "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),  # sandbox or live
    "client_id": os.environ.get('PAYPAL_CLIENT_ID', ''),
    "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET', '')
})

def create_payment(items, total, return_url, cancel_url, payer_email=None):
    """
    Create a PayPal payment
    
    Args:
        items (list): List of items in the format [{"name": "Book Title", "sku": "book-1", "price": "10.00", "currency": "USD", "quantity": 1}]
        total (float): Total payment amount
        return_url (str): URL to redirect after successful payment
        cancel_url (str): URL to redirect if payment is cancelled
        
    Returns:
        dict: Payment object or error message
    """
    # Determine currency preference: allow overriding via PAYPAL_CURRENCY env var
    currency = os.environ.get('PAYPAL_CURRENCY')
    if not currency:
        # Fallback: determine currency from items (assume all items use same currency)
        currency = items[0].get('currency', 'USD') if items else 'USD'

    payment_payload = {
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url
        },
        "transactions": [{
            "item_list": {
                "items": [{**dict(item), 'currency': currency} for item in items]
            },
            "amount": {
                "total": "{:.2f}".format(total),
                "currency": currency
            },
            "description": "Book purchase from Book Sales Website"
        }]
    }

    paypal_logger = logging.getLogger('paypal')
    paypal_logger.debug('Creating payment using currency=%s', currency)

    # If we have a payer email from the logged-in user, include it in the payload
    # PayPal may use this to pre-fill the buyer email on the approval page.
    if payer_email:
        try:
            payment_payload["payer"]["payer_info"] = {"email": payer_email}
        except Exception:
            pass

    payment = paypalrestsdk.Payment(payment_payload)
    if payment.create():
        # Log full payment object for debugging (server-side)
        try:
            paypal_logger.debug(f"Payment created: {payment.to_dict()}")
        except Exception:
            paypal_logger.debug(f"Payment created (no to_dict available): id={getattr(payment, 'id', None)}")

        # Extract approval URL
        for link in payment.links:
            if link.rel == "approval_url":
                return {"success": True, "payment_id": payment.id, "approval_url": link.href}
        return {"success": True, "payment_id": payment.id, "approval_url": None}
    else:
        try:
            paypal_logger.error(f"Payment creation failed: {payment.error}")
        except Exception:
            paypal_logger.error("Payment creation failed (no error payload)")
        return {"success": False, "error": payment.error}

def execute_payment(payment_id, payer_id):
    """
    Execute a PayPal payment after user approval
    
    Args:
        payment_id (str): PayPal payment ID
        payer_id (str): PayPal payer ID
        
    Returns:
        dict: Result of payment execution
    """
    payment = paypalrestsdk.Payment.find(payment_id)
    
    if payment.execute({"payer_id": payer_id}):
        return {"success": True, "payment": payment}
    else:
        return {"success": False, "error": payment.error}

def get_payment_details(payment_id):
    """
    Get details of a PayPal payment
    
    Args:
        payment_id (str): PayPal payment ID
        
    Returns:
        dict: Payment details
    """
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        return {"success": True, "payment": payment}
    except Exception as e:
        return {"success": False, "error": str(e)}
