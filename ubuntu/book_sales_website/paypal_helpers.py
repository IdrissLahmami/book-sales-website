"""
PayPal Integration Helper Module

This module provides helper functions for PayPal payment processing.
"""

import os
import paypalrestsdk
from flask import url_for, session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure PayPal
paypalrestsdk.configure({
    "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),  # sandbox or live
    "client_id": os.environ.get('PAYPAL_CLIENT_ID', ''),
    "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET', '')
})

def create_payment(items, total, return_url, cancel_url):
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
    payment = paypalrestsdk.Payment({
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
                "items": items
            },
            "amount": {
                "total": str(total),
                "currency": "USD"
            },
            "description": "Book purchase from Book Sales Website"
        }]
    })
    
    if payment.create():
        # Extract approval URL
        for link in payment.links:
            if link.rel == "approval_url":
                return {"success": True, "payment_id": payment.id, "approval_url": link.href}
    else:
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
