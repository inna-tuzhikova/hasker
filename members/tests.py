from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.urls import reverse

from .models import Member


class MemberModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password'
        )

    def test_add_invalid_member(self):
        with self.assertRaises(ValidationError):
            m = Member(
                user=self.user,
                avatar=123
            )
            m.full_clean()
            m.save()

    def test_add_valid_member(self):
        m = Member(user=self.user)
        m.save()


class MemberLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password'
        )
        member = Member(user=self.user)
        member.save()

    def test_invalid_login(self):
        response = self.client.post(
            reverse('login'),
            dict(
                username=self.user.username,
                password='invalid_password',
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

        response = self.client.post(
            reverse('login'),
            dict(
                username='invalid_login',
                password='invalid_password',
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_valid_login(self):
        response = self.client.post(
            reverse('login'),
            dict(
                username=self.user.username,
                password='test_password',
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_for_auth_user(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('login'),
            dict(
                username=self.user.username,
                password='test_password',
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)


class MemberLogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password'
        )
        member = Member(user=self.user)
        member.save()

    def test_user_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_logout_for_non_auth_user(self):
        response = self.client.post(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)


class MemberSignupViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password'
        )
        member = Member(user=self.user)
        member.save()

    def test_not_authorized_user(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_signup_with_existent_username(self):
        response = self.client.post(
            reverse('signup'),
            dict(
                username='test_user',
                email='email@email.com',
                password1='VeryStrongPassword',
                password2='VeryStrongPassword',
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_signup_with_very_long_username(self):
        response = self.client.post(
            reverse('signup'),
            dict(
                username='t' * 200,
                email='email@email.com',
                password1='VeryStrongPassword',
                password2='VeryStrongPassword',
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_signup_with_invalid_email(self):
        response = self.client.post(
            reverse('signup'),
            dict(
                username='another_test_user',
                email='invalid email fmt',
                password1='VeryStrongPassword',
                password2='VeryStrongPassword',
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_signup_with_wrong_confirmation_password(self):
        response = self.client.post(
            reverse('signup'),
            dict(
                username='another_test_user',
                email='email@email.com',
                password1='password1',
                password2='password2',
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_signup_with_unsafe_password(self):
        response = self.client.post(
            reverse('signup'),
            dict(
                username='another_test_user',
                email='email@email.com',
                password1='password',
                password2='password',
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_valid_signup(self):
        response = self.client.post(
            reverse('signup'),
            dict(
                username='another_test_user',
                email='email@email.com',
                password1='VeryStrongPassword',
                password2='VeryStrongPassword',
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.context['user'].username, 'another_test_user')
        self.assertTrue(response.context['user'].is_authenticated)


class MemberSettingsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password'
        )
        member = Member(user=self.user)
        member.save()

    def test_not_authorized_user(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 302)

    def test_invalid_settings_change(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('settings'),
            dict(
                email='invalid email fmt',
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'].errors)

    def test_valid_settings_change(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('settings'),
            dict(
                email='new_test@example.com',
            )
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new_test@example.com')
