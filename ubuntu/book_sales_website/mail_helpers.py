import os
import smtplib
from email.message import EmailMessage
from flask import render_template, current_app
from database_schema import User
import json
import requests
from datetime import datetime, timezone


def _get_smtp_config():
    return {
        'host': os.environ.get('SMTP_HOST', 'localhost'),
        'port': int(os.environ.get('SMTP_PORT', 25)),
        'user': os.environ.get('SMTP_USER'),
        'password': os.environ.get('SMTP_PASSWORD'),
        'use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
    }


def send_email(subject, to_address, html_body, text_body=None, from_address=None, role=None):
    cfg = _get_smtp_config()
    from_address = from_address or os.environ.get('SMTP_FROM', 'no-reply@example.com')

    # Prefer SendGrid if configured (API key present)
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    if sendgrid_api_key:
        try:
            _send_via_sendgrid(sendgrid_api_key, subject, to_address, html_body, text_body, from_address)
            current_app.logger.info(f"Sent invoice email to {to_address} via SendGrid subject={subject}")
            # append to debug log
            try:
                log_path = os.path.join(os.path.dirname(__file__), 'debug_email.log')
                with open(log_path, 'a', encoding='utf-8') as lf:
                    lf.write(f"{datetime.now(timezone.utc).isoformat()}\tSendGrid\t{role or ''}\t{to_address}\t{subject}\n")
            except Exception:
                current_app.logger.exception('Failed to write debug_email.log')
            return
        except Exception:
            current_app.logger.exception(f"SendGrid send failed for {to_address}, falling back to SMTP")

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address

    if text_body:
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype='html')
    else:
        # If no text provided, put HTML as alternative
        msg.set_content('This email contains HTML content. Please view in an HTML-capable client.')
        msg.add_alternative(html_body, subtype='html')

    try:
        if cfg['use_tls']:
            with smtplib.SMTP(cfg['host'], cfg['port']) as smtp:
                smtp.starttls()
                if cfg['user'] and cfg['password']:
                    smtp.login(cfg['user'], cfg['password'])
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(cfg['host'], cfg['port']) as smtp:
                if cfg['user'] and cfg['password']:
                    smtp.login(cfg['user'], cfg['password'])
                smtp.send_message(msg)
        current_app.logger.info(f"Sent invoice email to {to_address} subject={subject}")
        # append to debug log
        try:
            log_path = os.path.join(os.path.dirname(__file__), 'debug_email.log')
            with open(log_path, 'a', encoding='utf-8') as lf:
                lf.write(f"{datetime.now(timezone.utc).isoformat()}\tSMTP\t{role or ''}\t{to_address}\t{subject}\n")
        except Exception:
            current_app.logger.exception('Failed to write debug_email.log')
    except Exception:
        current_app.logger.exception(f"Failed to send email to {to_address}")


def _send_via_sendgrid(api_key, subject, to_address, html_body, text_body, from_address):
    """Send an email using SendGrid Web API v3."""
    url = 'https://api.sendgrid.com/v3/mail/send'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    # Build payload according to SendGrid API
    payload = {
        'personalizations': [
            {'to': [{'email': to_address}]}
        ],
        'from': {'email': from_address},
        'subject': subject,
        'content': []
    }
    if text_body:
        payload['content'].append({'type': 'text/plain', 'value': text_body})
    else:
        payload['content'].append({'type': 'text/plain', 'value': 'Please view this email in an HTML-capable client.'})
    payload['content'].append({'type': 'text/html', 'value': html_body})

    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    if resp.status_code >= 400:
        # raise an informative exception for caller to log
        raise RuntimeError(f"SendGrid API error {resp.status_code}: {resp.text}")


def send_order_invoices(order):
    """Render invoice templates and send to customer and merchant.

    Expects `order` to be an Order instance with `user_id`, `id`, `total_amount`,
    and related OrderItem rows available via relationship or separate queries.
    """
    try:
        user = User.query.get(order.user_id)
        customer_email = getattr(user, 'email', None)

        # Render templates (uses Flask template system)
        html = render_template('emails/invoice.html', order=order, user=user)
        text = render_template('emails/invoice.txt', order=order, user=user)

        # Send to customer
        if customer_email:
            send_email(subject=f"Your Invoice - Order #{order.id}",
                       to_address=customer_email,
                       html_body=html,
                       text_body=text,
                       role='customer')

        # Send to merchant: prefer an admin user's email from the DB, fall back to
        # MERCHANT_EMAIL env var if present.
        merchant_email = None
        admin_user = User.query.filter_by(is_admin=True).first()
        if admin_user and getattr(admin_user, 'email', None):
            merchant_email = admin_user.email
        else:
            merchant_email = os.environ.get('MERCHANT_EMAIL')

        if merchant_email:
            send_email(subject=f"New Order Received - #{order.id}",
                       to_address=merchant_email,
                       html_body=html,
                       text_body=text,
                       from_address=customer_email or None,
                       role='merchant')

    except Exception:
        current_app.logger.exception('Failed to render/send order invoices')
