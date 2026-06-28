from datetime import datetime

from ninja.responses import NinjaJSONEncoder


class JsonEncoder(NinjaJSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return super().default(o)
