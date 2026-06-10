import os
import asyncio
import shlex
import smtplib
from html import escape
from email.message import EmailMessage
from flask import render_template, current_app
from database_schema import User
import json
import requests
from datetime import datetime, timezone

try:
    from mcp import ClientSession, stdio_client
    from mcp.client.stdio import StdioServerParameters
except Exception:
    ClientSession = None
    stdio_client = None
    StdioServerParameters = None


def _get_smtp_config():
    return {
        'host': os.environ.get('SMTP_HOST', 'localhost'),
        'port': int(os.environ.get('SMTP_PORT', 25)),
        'user': os.environ.get('SMTP_USER'),
        'password': os.environ.get('SMTP_PASSWORD'),
        'use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
    }


def _append_debug_email_log(transport, role, to_address, subject):
    try:
        log_path = os.path.join(os.path.dirname(__file__), 'debug_email.log')
        with open(log_path, 'a', encoding='utf-8') as lf:
            lf.write(f"{datetime.now(timezone.utc).isoformat()}\t{transport}\t{role or ''}\t{to_address}\t{subject}\n")
    except Exception:
        current_app.logger.exception('Failed to write debug_email.log')


def _get_email_provider():
    return os.environ.get('EMAIL_PROVIDER', 'auto').strip().lower()


def send_email(subject, to_address, html_body, text_body=None, from_address=None, role=None):
    cfg = _get_smtp_config()
    from_address = (
        from_address
        or os.environ.get('SENDER_EMAIL_ADDRESS')
        or os.environ.get('SMTP_FROM', 'no-reply@example.com')
    )
    provider = _get_email_provider()

    # If EMAIL_PROVIDER=mcp (or auto), try MCP stdio first.
    if provider in ('auto', 'mcp'):
        try:
            _send_via_mcp_send_email(subject, to_address, html_body, text_body, from_address)
            current_app.logger.info(f"Sent invoice email to {to_address} via MCP subject={subject}")
            _append_debug_email_log('MCP', role, to_address, subject)
            return
        except Exception:
            if provider == 'mcp':
                current_app.logger.exception(
                    f"MCP email send failed for {to_address}, falling back to configured backups"
                )
            else:
                current_app.logger.exception(
                    f"MCP email provider unavailable for {to_address}, trying SendGrid/SMTP"
                )

    # Prefer SendGrid when provider allows it and API key is present.
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    if provider in ('auto', 'sendgrid') and sendgrid_api_key:
        try:
            _send_via_sendgrid(sendgrid_api_key, subject, to_address, html_body, text_body, from_address)
            current_app.logger.info(f"Sent invoice email to {to_address} via SendGrid subject={subject}")
            _append_debug_email_log('SendGrid', role, to_address, subject)
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
        _append_debug_email_log('SMTP', role, to_address, subject)
    except Exception:
        current_app.logger.exception(f"Failed to send email to {to_address}")


def _send_via_mcp_send_email(subject, to_address, html_body, text_body, from_address):
    if not (ClientSession and stdio_client and StdioServerParameters):
        raise RuntimeError('MCP client package is not installed')

    command = os.environ.get('MCP_EMAIL_SERVER_COMMAND', 'npx').strip()
    args_raw = os.environ.get('MCP_EMAIL_SERVER_ARGS', '-y resend-mcp')
    args = shlex.split(args_raw, posix=False)
    configured_tool_name = os.environ.get('MCP_EMAIL_TOOL_NAME', '').strip()

    def _flatten_mcp_result_text(result):
        parts = []
        content = getattr(result, 'content', []) or []
        for item in content:
            text = getattr(item, 'text', None)
            if text:
                parts.append(str(text))
        if parts:
            return "\n".join(parts)
        structured = getattr(result, 'structuredContent', None)
        if structured is not None:
            try:
                return json.dumps(structured)
            except Exception:
                return str(structured)
        return str(result)

    async def _send():
        server = StdioServerParameters(
            command=command,
            args=args,
            env=dict(os.environ),
        )

        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                tools_result = await session.list_tools()
                tools = getattr(tools_result, 'tools', []) or []
                if not tools:
                    raise RuntimeError('MCP email server exposed no tools')

                selected_tool = None
                if configured_tool_name:
                    for tool in tools:
                        if getattr(tool, 'name', '') == configured_tool_name:
                            selected_tool = tool
                            break

                if selected_tool is None:
                    for tool in tools:
                        name = (getattr(tool, 'name', '') or '').lower()
                        if 'send' in name and 'email' in name:
                            selected_tool = tool
                            break

                if selected_tool is None:
                    selected_tool = tools[0]

                input_schema = getattr(selected_tool, 'inputSchema', {}) or {}
                schema_props = (input_schema.get('properties') if isinstance(input_schema, dict) else {}) or {}

                request_args = {
                    'to': to_address,
                    'to_email': to_address,
                    'recipient': to_address,
                    'recipient_email': to_address,
                    'subject': subject,
                    'html': html_body,
                    'html_body': html_body,
                    'body_html': html_body,
                    'text': text_body or 'Please view this email in an HTML-capable client.',
                    'text_body': text_body or 'Please view this email in an HTML-capable client.',
                    'body_text': text_body or 'Please view this email in an HTML-capable client.',
                    'from': from_address,
                    'from_email': from_address,
                    'sender': from_address,
                }

                if schema_props:
                    filtered_args = {}
                    for key, prop in schema_props.items():
                        if key not in request_args:
                            continue

                        value = request_args[key]
                        prop_type = prop.get('type') if isinstance(prop, dict) else None

                        # Resend MCP `send-email` expects `to` as an array.
                        if key == 'to' and prop_type == 'array' and isinstance(value, str):
                            value = [value]

                        filtered_args[key] = value
                    call_args = filtered_args
                else:
                    call_args = {
                        'to': to_address,
                        'subject': subject,
                        'html': html_body,
                        'text': text_body or 'Please view this email in an HTML-capable client.',
                        'from': from_address,
                    }

                result = await session.call_tool(selected_tool.name, call_args)
                if getattr(result, 'isError', False):
                    details = _flatten_mcp_result_text(result)
                    raise RuntimeError(f"MCP tool '{selected_tool.name}' returned error: {details}")

    asyncio.run(_send())


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


def _format_order_date(order):
    if getattr(order, 'order_date', None):
        return order.order_date.strftime('%Y-%m-%d %H:%M')
    return ''


def _build_resend_invoice_variables(order, user, pathway):
    items_rows = []
    for item in getattr(order, 'items', []) or []:
        title = escape(getattr(getattr(item, 'book', None), 'title', 'Book'))
        qty = int(getattr(item, 'quantity', 0) or 0)
        price = float(getattr(item, 'price', 0) or 0)
        line_total = price * qty
        items_rows.append(
            f"<tr><td style='padding:10px;border-bottom:1px solid #e5e7eb'>{title}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #e5e7eb;text-align:center'>{qty}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #e5e7eb;text-align:right'>£{price:.2f}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #e5e7eb;text-align:right'>£{line_total:.2f}</td></tr>"
        )

    if not items_rows:
        items_rows.append(
            "<tr><td colspan='4' style='padding:10px;border-bottom:1px solid #e5e7eb'>"
            "No items available.</td></tr>"
        )

    return {
        'PATHWAY': pathway,
        'ORDER_ID': int(getattr(order, 'id', 0) or 0),
        'ORDER_DATE': _format_order_date(order),
        'CUSTOMER_NAME': escape(getattr(user, 'name', '') or 'Customer'),
        'CUSTOMER_EMAIL': escape(getattr(user, 'email', '') or ''),
        'ORDER_TOTAL': f"{float(getattr(order, 'total_amount', 0) or 0):.2f}",
        'ITEM_ROWS': ''.join(items_rows),
    }


def _send_via_resend_template(api_key, template_id, to_address, subject, from_address, variables):
    payload = {
        'from': from_address,
        'to': [to_address],
        'subject': subject,
        'template': {
            'id': template_id,
            'variables': variables,
        },
    }

    resp = requests.post(
        'https://api.resend.com/emails',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=20,
    )

    if resp.status_code >= 400:
        raise RuntimeError(f"Resend template send error {resp.status_code}: {resp.text}")


def send_order_invoices(order):
    """Render invoice templates and send to customer and merchant.

    Expects `order` to be an Order instance with `user_id`, `id`, `total_amount`,
    and related OrderItem rows available via relationship or separate queries.
    """
    try:
        user = User.query.get(order.user_id)
        customer_email = getattr(user, 'email', None)
        resend_template_id = os.environ.get('RESEND_INVOICE_TEMPLATE_ID', '').strip()
        resend_api_key = os.environ.get('RESEND_API_KEY', '').strip()

        # For paid invoice testing only: reroute to the allowed Resend test inbox.
        is_paid_invoice = float(getattr(order, 'total_amount', 0) or 0) > 0
        customer_subject_prefix = ''
        if is_paid_invoice and customer_email == 'test-invoice@example.com':
            customer_email = 'irl2010@live.co.uk'
            customer_subject_prefix = '[CUSTOMER] '

        # Render templates (uses Flask template system)
        html = render_template('emails/invoice.html', order=order, user=user)
        text = render_template('emails/invoice.txt', order=order, user=user)

        # Send to customer
        if customer_email:
            subject = f"{customer_subject_prefix}Your Invoice - Order #{order.id}"
            if resend_template_id and resend_api_key:
                try:
                    _send_via_resend_template(
                        api_key=resend_api_key,
                        template_id=resend_template_id,
                        to_address=customer_email,
                        subject=subject,
                        from_address=os.environ.get('SENDER_EMAIL_ADDRESS') or os.environ.get('SMTP_FROM', 'no-reply@example.com'),
                        variables=_build_resend_invoice_variables(order, user, 'customer'),
                    )
                    current_app.logger.info(f"Sent invoice email to {customer_email} via Resend template subject={subject}")
                    _append_debug_email_log('RESEND_TEMPLATE', 'customer', customer_email, subject)
                except Exception:
                    current_app.logger.exception(f"Resend template send failed for {customer_email}, falling back to default transport")
                    send_email(subject=subject,
                               to_address=customer_email,
                               html_body=html,
                               text_body=text,
                               role='customer')
            else:
                send_email(subject=subject,
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

        merchant_subject_prefix = ''
        if is_paid_invoice and merchant_email == 'admin@example.com':
            merchant_email = 'irl2010@live.co.uk'
            merchant_subject_prefix = '[MERCHANT] '

        if merchant_email:
            subject = f"{merchant_subject_prefix}New Order Received - #{order.id}"
            if resend_template_id and resend_api_key:
                try:
                    _send_via_resend_template(
                        api_key=resend_api_key,
                        template_id=resend_template_id,
                        to_address=merchant_email,
                        subject=subject,
                        from_address=os.environ.get('SENDER_EMAIL_ADDRESS') or os.environ.get('SMTP_FROM', 'no-reply@example.com'),
                        variables=_build_resend_invoice_variables(order, user, 'merchant'),
                    )
                    current_app.logger.info(f"Sent invoice email to {merchant_email} via Resend template subject={subject}")
                    _append_debug_email_log('RESEND_TEMPLATE', 'merchant', merchant_email, subject)
                except Exception:
                    current_app.logger.exception(f"Resend template send failed for {merchant_email}, falling back to default transport")
                    send_email(subject=subject,
                               to_address=merchant_email,
                               html_body=html,
                               text_body=text,
                               from_address=customer_email or None,
                               role='merchant')
            else:
                send_email(subject=subject,
                           to_address=merchant_email,
                           html_body=html,
                           text_body=text,
                           from_address=customer_email or None,
                           role='merchant')

    except Exception:
        current_app.logger.exception('Failed to render/send order invoices')
