import boto3
import json

import os

from flask import render_template
from flask.ext.mail import Message

from app import create_app

from . import mail


def send_email_func(event=None, context=None):
    if not event:
        event = dict()

    recipient = event.get('recipient')
    subject = event.get('subject')
    template = event.get('template')

    kwargs = [{k: v} for k, v in event.items() if k not in ['recipient', 'subject', 'template']]

    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        msg = Message(
            app.config['EMAIL_SUBJECT_PREFIX'] + ' ' + subject,
            sender=app.config['EMAIL_SENDER'],
            recipients=[recipient])
        msg.body = render_template(template + '.txt', context=kwargs)
        msg.html = render_template(template + '.html', context=kwargs)
        mail.send(msg)


def send_email(recipient, subject, template, **kwargs):

    event = {'recipient': recipient,
             'subject': subject,
             'template': template}
    event.update(**kwargs)

    if hasattr(Config, 'DEBUG'):
        return send_email_func(event=event)
    else:
        client = boto3.client('lambda')
        client.invoke(
            FunctionName='flask-base.app.email.send_email_func',
            InvocationType='Event',
            Payload=json.dumps(event)
        )
