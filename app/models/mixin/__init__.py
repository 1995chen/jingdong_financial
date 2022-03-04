# -*- coding: utf-8 -*-


from datetime import datetime


class ToDictMixin(object):
    # do not use it directly
    def to_dict(self):
        res = {}
        if hasattr(self, "dict_keys"):
            keys = self.dict_keys
            for c in keys:
                v = getattr(self, c, None)
                if isinstance(v, datetime):
                    res.update({c: v.strftime("%Y-%m-%d %H:%M:%S")})
                else:
                    res.update({c: v})
        else:
            keys = self.__table__.columns
            for c in keys:
                v = getattr(self, c.name, None)
                if isinstance(v, datetime):
                    res.update({c.name: v.strftime("%Y-%m-%d %H:%M:%S")})
                else:
                    res.update({c.name: v})
        return res
