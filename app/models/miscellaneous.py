from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from flask import current_app


class EditableHTML(Model):
    class Meta:
        table_name = 'editors'
        host = current_app.config['DYNAMO_URL']
        read_capacity_units = 1
        write_capacity_units = 1

    # id = db.Column(db.Integer, primary_key=True)
    editor_name = UnicodeAttribute(hash_key=True)  # editor_name = db.Column(db.String(100), unique=True)
    value = UnicodeAttribute(default=' ')  # value = db.Column(db.Text)

    @staticmethod
    def get_editable_html(editor_name):
        editable_html_obj = EditableHTML.get(editor_name)  # editable_html_obj = EditableHTML.query.filter_by(editor_name=editor_name).first()

        if editable_html_obj is None:
            editable_html_obj = EditableHTML(editor_name=editor_name, value=' ')
        return editable_html_obj
