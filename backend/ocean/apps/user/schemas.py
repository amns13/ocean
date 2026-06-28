from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema

User = get_user_model()


class UserLoginSchemaIn(Schema):
    username: str
    password: str


class UserDetailsSchema(ModelSchema):
    class Meta:
        model = User
        fields = ("uid", "username", "email")
