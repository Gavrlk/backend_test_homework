from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="User1")
        self.user2 = User.objects.create(username="User2")

        self.note1 = Note.objects.create(
            title="User1 Note",
            text="Text 1",
            slug="user1-note",
            author=self.user1
        )

        self.note2 = Note.objects.create(
            title="User1 Note 2",
            text="Text 2",
            slug="user1-note-2",
            author=self.user1
        )

        self.note3 = Note.objects.create(
            title="User2 Note",
            text="Text 3",
            slug="user2-note",
            author=self.user2
        )

    def test_note_in_object_list_on_notes_list_page(self):
        """Отдельная заметка передаётся на страницу со списком заметок"""
        self.client.force_login(self.user1)
        url = reverse("notes:list")
        response = self.client.get(url)

        object_list = response.context["object_list"]
        self.assertIn(self.note1, object_list)
        self.assertIn(self.note2, object_list)
        self.assertEqual(len(object_list), 2)

    def test_notes_do_not_mix_between_users(self):
        """В список заметок одного пользователя не попадают заметки другого"""
        self.client.force_login(self.user1)
        url = reverse("notes:list")
        response = self.client.get(url)

        object_list = response.context["object_list"]
        self.assertNotIn(self.note3, object_list)

        self.client.force_login(self.user2)
        response = self.client.get(url)
        object_list = response.context["object_list"]
        self.assertIn(self.note3, object_list)
        self.assertNotIn(self.note1, object_list)
        self.assertNotIn(self.note2, object_list)

    def test_form_on_create_page(self):
        """На страницу создания заметки передаётся форма"""
        self.client.force_login(self.user1)
        url = reverse("notes:add")
        response = self.client.get(url)

        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], NoteForm)

    def test_form_on_edit_page(self):
        """На страницу редактирования заметки передаётся форма"""
        self.client.force_login(self.user1)
        url = reverse("notes:edit", args=[self.note1.slug])
        response = self.client.get(url)

        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], NoteForm)
        self.assertEqual(response.context["form"].instance, self.note1)
