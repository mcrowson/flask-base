from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from flask import current_app
import os


class EditableHTML(Model):
    class Meta:
        table_name = 'editors'
        host = os.environ.get('DYNAMO_URL')  # This should not be fished out of the env but from the app
        read_capacity_units = 1
        write_capacity_units = 1

    editor_name = UnicodeAttribute(hash_key=True)
    value = UnicodeAttribute(default=' ')

    @staticmethod
    def get_editable_html(editor_name):
        editable_html_obj = EditableHTML.get(editor_name)

        if editable_html_obj is None:
            editable_html_obj = EditableHTML(editor_name=editor_name, value=' ')
        return editable_html_obj
