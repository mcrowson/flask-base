from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from flask import current_app
import os


class Session(Model):
    class Meta:
        table_name = 'session'
        host = os.environ.get('DYNAMO_URL')  # This should not be fished out of the env but from the app
        read_capacity_units = 1
        write_capacity_units = 1

    session_id = UnicodeAttribute(hash_key=True)
    value = UnicodeAttribute(default=' ')
