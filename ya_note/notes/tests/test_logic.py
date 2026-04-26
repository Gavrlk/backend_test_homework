from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.another_user = User.objects.create(username="AnotherUser")
        self.valid_form_data = {
            "title": "New Note",
            "text": "This is a new note",
            "slug": "new-note"
        }

    def test_authenticated_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку"""
        self.client.force_login(self.user)
        url = reverse("notes:add")
        response = self.client.post(url, data=self.valid_form_data)
        self.assertRedirects(response, reverse("notes:success"))
        self.assertTrue(Note.objects.filter(slug="new-note").exists())
        note = Note.objects.get(slug="new-note")
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.title, "New Note")

    def test_anonymous_user_cannot_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        url = reverse("notes:add")
        response = self.client.post(url, data=self.valid_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.filter(slug="new-note").exists())

    def test_cannot_create_two_notes_with_same_slug(self):
        """Невозможно создать две заметки с одинаковым slug"""
        self.client.force_login(self.user)
        response1 = self.client.post(
            reverse("notes:add"),
            data=self.valid_form_data
        )
        self.assertEqual(response1.status_code, 302)

        response2 = self.client.post(
            reverse("notes:add"),
            data=self.valid_form_data
        )
        self.assertEqual(response2.status_code, 200)
        self.assertTrue(response2.context['form'].errors)
        self.assertIn('slug', response2.context['form'].errors)
        self.assertEqual(Note.objects.filter(slug="new-note").count(), 1)

    def test_slug_auto_created_from_title_if_empty(self):
        """Если slug не заполнен, он формируется автоматически"""
        self.client.force_login(self.user)
        form_data = self.valid_form_data.copy()
        form_data["slug"] = ""
        form_data["title"] = "My Awesome Note With Spaces"
        response = self.client.post(reverse("notes:add"), data=form_data)
        self.assertRedirects(response, reverse("notes:success"))
        note = Note.objects.latest("id")
        self.assertTrue(note.slug)  # Проверяем, что slug не пустой
        self.assertNotEqual(note.slug, "")  # slug автоматически заполнен


class TestNoteEditDelete(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="User")
        self.another_user = User.objects.create(username="AnotherUser")
        self.note = Note.objects.create(
            title="Original Title",
            text="Original text",
            slug="original-slug",
            author=self.user
        )
        self.edit_data = {
            "title": "Updated Title",
            "text": "Updated text",
            "slug": "updated-slug"
        }

    def test_user_can_edit_own_note(self):
        """Пользователь может редактировать свои заметки"""
        self.client.force_login(self.user)
        url = reverse("notes:edit", args=[self.note.slug])
        response = self.client.post(url, data=self.edit_data)
        self.assertRedirects(response, reverse("notes:success"))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "Updated Title")
        self.assertEqual(self.note.text, "Updated text")

    def test_user_cannot_edit_others_note(self):
        """Пользователь не может редактировать чужие заметки"""
        self.client.force_login(self.another_user)
        url = reverse("notes:edit", args=[self.note.slug])
        response = self.client.post(url, data=self.edit_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "Original Title")

    def test_user_can_delete_own_note(self):
        """Пользователь может удалять свои заметки"""
        self.client.force_login(self.user)
        url = reverse("notes:delete", args=[self.note.slug])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("notes:success"))
        self.assertFalse(Note.objects.filter(slug="original-slug").exists())

    def test_user_cannot_delete_others_note(self):
        """Пользователь не может удалять чужие заметки"""
        self.client.force_login(self.another_user)
        url = reverse("notes:delete", args=[self.note.slug])
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Note.objects.filter(slug="original-slug").exists())
