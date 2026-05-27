#!/usr/bin/env python3
"""
Create a sample order and send invoice emails for local testing.

Usage:
  python create_test_order_and_send.py [--user-email email] [--book-id id]

This script must be run from the `book_sales_website/scripts` directory or with
the project root on PYTHONPATH. It will import the Flask app and run inside
an application context.
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database_schema import db, User, Book, Order, OrderItem, Payment
from mail_helpers import send_order_invoices
from werkzeug.security import generate_password_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user-email', default=os.environ.get('TEST_USER_EMAIL', 'test-invoice@example.com'))
    parser.add_argument('--book-id', type=int, default=None)
    args = parser.parse_args()

    with app.app_context():
        # Find or create user
        user = User.query.filter_by(email=args.user_email).first()
        if not user:
            user = User(email=args.user_email, name='Test User', password=generate_password_hash('Test1234'))
            db.session.add(user)
            db.session.commit()
            print(f'Created test user: {user.email} (id={user.id})')
        else:
            print(f'Using existing user: {user.email} (id={user.id})')

        # Select a book
        book = None
        if args.book_id:
            book = Book.query.get(args.book_id)
            if not book:
                print(f'Book id {args.book_id} not found; falling back to first available')

        if not book:
            book = Book.query.filter_by(is_available=True).first()
            if not book:
                print('No available books found. Please add a Book row to the database first.')
                return

        # Create order
        order = Order(user_id=user.id, total_amount=book.price, status='completed')
        db.session.add(order)
        db.session.flush()  # to get order.id

        order_item = OrderItem(order_id=order.id, book_id=book.id, quantity=1, price=book.price)
        db.session.add(order_item)

        payment = Payment(order_id=order.id, amount=book.price, payment_method='test', transaction_id='TESTTXN', status='completed')
        db.session.add(payment)

        db.session.commit()
        print(f'Created test order {order.id} for user {user.email} book {book.title}')

        # Send invoices
        try:
            send_order_invoices(order)
            print('Invoice emails triggered (check SMTP output / logs).')
        except Exception:
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
