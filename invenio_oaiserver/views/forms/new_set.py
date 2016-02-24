from flask import (Blueprint,
                   render_template,
                   request,
                   flash,
                   redirect,
                   url_for,
                   current_app)
from invenio_oaiserver.models import OAISet
from wtforms import Form, fields, validators, ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField


def get_NewSetForm(*args, **kwargs):
    def query_or_collection_check(form, field):
        if field and form.collection:
            raise ValidationError('There can be only one field given from: query, collection')

    class NewSetForm(Form):
        # sets = [(set.name, set.name) for set in Set.query.all()]
        # sets.insert(0, (0, "No parent set"))

        spec = fields.StringField(
            'Set spec',
            description="Unique set name",
            validators=[validators.InputRequired()],
        )
        name = fields.StringField(
            'Set name',
            description="Human readable set name",
            validators=[validators.InputRequired()],
        )
        description = fields.StringField(
            'Description',
            description="Short description of set"
        )
        search_pattern = fields.StringField(
            'Query',
            description="Query to match records",
            validators=[validators.InputRequired()]  # query_or_collection_check]
        )

    return NewSetForm(*args, **kwargs)
