import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    class Meta:
        model = User
