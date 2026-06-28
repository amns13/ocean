from ninja.renderers import JSONRenderer

from ocean.utils.encoders import JsonEncoder


class CustomJsonRender(JSONRenderer):
    encoder_class = JsonEncoder
