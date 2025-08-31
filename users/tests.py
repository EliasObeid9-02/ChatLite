from django.contrib.auth import get_user_model
from django.test import TestCase

UserModel = get_user_model()


class UserModelsTest(TestCase):
    def test_create_user(self):
        user = UserModel.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.assertIsNotNone(user.pk)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("password123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_no_email(self):
        with self.assertRaises(ValueError):
            UserModel.objects.create_user(
                username="testuser", email="", password="password123"
            )

    def test_create_user_no_username(self):
        with self.assertRaises(ValueError):
            UserModel.objects.create_user(
                username="", email="test@example.com", password="password123"
            )

    def test_create_superuser(self):
        superuser = UserModel.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )
        self.assertIsNotNone(superuser.pk)
        self.assertEqual(superuser.username, "admin")
        self.assertEqual(superuser.email, "admin@example.com")
        self.assertTrue(superuser.check_password("adminpass"))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_superuser_no_is_staff(self):
        with self.assertRaises(ValueError):
            UserModel.objects.create_superuser(
                username="admin2",
                email="admin2@example.com",
                password="adminpass",
                is_staff=False,
            )

    def test_create_superuser_no_is_superuser(self):
        with self.assertRaises(ValueError):
            UserModel.objects.create_superuser(
                username="admin3",
                email="admin3@example.com",
                password="adminpass",
                is_superuser=False,
            )

    def test_user_str_representation(self):
        user = UserModel.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.assertEqual(str(user), "testuser")

    def test_user_profile_creation_on_user_save(self):
        user = UserModel.objects.create_user(
            username="profileuser", email="profile@example.com", password="password123"
        )
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.display_name, "profileuser")
        self.assertIsNone(user.profile.profile_picture)

    def test_user_profile_update_on_user_save(self):
        user = UserModel.objects.create_user(
            username="updateuser", email="update@example.com", password="password123"
        )
        user.profile.display_name = "Updated Name"
        user.profile.save()
        user.save()  # Trigger the signal again
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.display_name, "Updated Name")

    def test_user_profile_str_representation(self):
        user = UserModel.objects.create_user(
            username="profileuser2",
            email="profile2@example.com",
            password="password123",
        )
        self.assertEqual(str(user.profile), f"{user}: {user.profile.display_name}")
