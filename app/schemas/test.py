# -*- coding: utf-8 -*-


from marshmallow import Schema, fields, validate


class TestSchema(Schema):
    position = fields.String(allow_none=False, validate=validate.OneOf(('left', 'right')))
    head = fields.String(allow_none=False)
