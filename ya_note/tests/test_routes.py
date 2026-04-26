from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class RoutesTestCase(TestCase):
    def setUp(self):
        self.auth_user = User.objects.create(username="TestUser")
        self.another_user = User.objects.create(username="AnotherUser")

        from notes.models import Note
        self.note = Note.objects.create(
            title="Test Note",
            text="Test text",
            slug="test-note",
            author=self.auth_user
        )

    def test_home_page_available_to_anonymous(self):
        url = reverse("notes:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_notes_list_available_to_authenticated_user(self):
        url = reverse("notes:list")
        self.client.force_login(self.auth_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_page_done(self):
        url = reverse("notes:success")
        self.client.force_login(self.auth_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_add(self):
        url = reverse("notes:add")
        self.client.force_login(self.auth_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_detail_available_only_to_author(self):
        """Страница отдельной заметки доступна только автору"""
        url = reverse("notes:detail", args=[self.note.slug])

        self.client.force_login(self.auth_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.client.force_login(self.another_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_note_edit_available_only_to_author(self):
        """Страница редактирования заметки доступна только автору"""
        url = reverse("notes:edit", args=[self.note.slug])

        self.client.force_login(self.auth_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.client.force_login(self.another_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_note_delete_available_only_to_author(self):
        """Страница удаления заметки доступна только автору"""
        url = reverse("notes:delete", args=[self.note.slug])

        self.client.force_login(self.auth_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.client.force_login(self.another_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_anonymous_redirected_to_login_for_notes_list(self):
        """Анонимный пользователь перенаправляется на страницу логина"""
        url = reverse("notes:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_redirected_to_login_for_success_page(self):
        """Анонимный пользователь перенаправляется на страницу логина"""
        url = reverse("notes:success")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith('/auth/login/')
            or response.url.startswith('/accounts/login/')
        )

    def test_anonymous_redirected_to_login_for_add_page(self):
        """Анонимный пользователь перенаправляется на страницу логина"""
        url = reverse("notes:add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_redirected_to_login_for_detail_page(self):
        """Анонимный пользователь перенаправляется на страницу логина"""
        url = reverse("notes:detail", args=[self.note.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_redirected_to_login_for_edit_page(self):
        """Анонимный пользователь перенаправляется на страницу логина"""
        url = reverse("notes:edit", args=[self.note.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_redirected_to_login_for_delete_page(self):
        """Анонимный пользователь перенаправляется на страницу логина"""
        url = reverse("notes:delete", args=[self.note.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_auth_pages_available_to_all_users(self):
        """Страницы регистрации, входа и выхода доступны всем пользователям"""
        # Страница регистрации
        response = self.client.get(reverse("users:signup"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Страница входа
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.client.get(reverse("users:logout"))
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        # POST запрос к странице выхода
        response = self.client.post(reverse("users:logout"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
