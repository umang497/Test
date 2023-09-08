from django.test import TestCase

from django.urls import reverse

from userman.models import User, UserLevel


class UserValidationTests(TestCase):
    def create_user(self, username, password, name, phone_number):
        return self.client.post(
            path=reverse('register_user'),
            data={
                'username': username,
                'password': password,
                'name': name,
                'phone_number': phone_number
            }
        )

    def test_create_user_required_fields(self):
        response = self.create_user("", "somepassword", "Batman", "9876543211")
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'message': {'username': ['This field may not be blank.']}})

        response = self.create_user("someuser", "", "Batman", "9876543211")
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'message': {'password': ['This field may not be blank.']}})

        response = self.create_user("someuser", "somepassword", "", "9876543211")
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'message': {'name': ['This field may not be blank.']}})

        response = self.create_user("someuser", "somepassword", "Batman", "")
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'message': {'phone_number': ['This field may not be blank.']}})

    def test_create_user_successful(self):
        response = self.create_user("someuser", "somepassword", "Batman", "9876543211")
        self.assertEquals(response.status_code, 201)

        user = User.objects.get(username="someuser")
        self.assertEquals(user.user_level, UserLevel.REGULAR)
        self.assertEquals(user.phone_number, "9876543211")
        self.assertEquals(user.name, "Batman")
        # Not storing raw password
        self.assertNotEquals(user.password, "somepassword")

    def test_duplicate_username(self):
        self.test_create_user_successful()
        response = self.create_user("someuser", "somepassword", "Batman", "9876543211")
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'message': {'username': ['user with this username already exists.']}})
