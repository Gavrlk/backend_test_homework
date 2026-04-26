import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client
from http import HTTPStatus

from news.models import News, Comment
from news.forms import BAD_WORDS

User = get_user_model()


@pytest.mark.django_db
class TestCommentLogic:
    def setup_method(self):
        """Подготовка данных перед каждым тестом"""
        self.user = User.objects.create(username='TestUser')
        self.another_user = User.objects.create(username='AnotherUser')
        self.client = Client()
        self.news = News.objects.create(
            title='Test News',
            text='Test text',
            date='2024-01-01'
        )
        self.comment = Comment.objects.create(
            news=self.news,
            author=self.user,
            text='Original comment'
        )
        self.valid_comment_data = {
            'text': 'This is a valid comment'
        }

    def test_anonymous_user_cannot_send_comment(self):
        """Анонимный пользователь не может отправить комментарий"""
        url = reverse('news:detail', args=[self.news.pk])
        response = self.client.post(url, data=self.valid_comment_data)
        assert response.status_code == HTTPStatus.FOUND
        assert '/auth/login/' in response.url
        assert (
            Comment.objects.filter(text='This is a valid comment').count() == 0
        )

    def test_authenticated_user_can_send_comment(self):
        """Авторизованный пользователь может отправить комментарий"""
        self.client.force_login(self.user)
        url = reverse('news:detail', args=[self.news.pk])
        response = self.client.post(url, data=self.valid_comment_data)
        assert response.status_code == HTTPStatus.FOUND
        assert reverse('news:detail', args=[self.news.pk]) in response.url
        assert (
            Comment.objects.filter(text='This is a valid comment').count() == 1
        )
        comment = Comment.objects.get(text='This is a valid comment')
        assert comment.author == self.user
        assert comment.news == self.news

    def test_comment_with_bad_words_not_published(self):
        """
        Если комментарий содержит запрещённые слова,
        он не будет опубликован
        """
        self.client.force_login(self.user)
        url = reverse('news:detail', args=[self.news.pk])
        for bad_word in BAD_WORDS:
            bad_comment_data = {'text': f'This is a {bad_word} comment'}
            response = self.client.post(url, data=bad_comment_data)
            assert response.status_code == HTTPStatus.OK
            assert 'form' in response.context
            assert response.context['form'].errors
            assert Comment.objects.filter(text__contains=bad_word).count() == 0

    def test_user_can_edit_own_comment(self):
        """Авторизованный пользователь может редактировать свои комментарии"""
        self.client.force_login(self.user)
        url = reverse('news:edit', args=[self.comment.pk])
        edit_data = {'text': 'Updated comment text'}
        response = self.client.post(url, data=edit_data)
        assert response.status_code == HTTPStatus.FOUND
        assert reverse('news:detail', args=[self.news.pk]) in response.url
        self.comment.refresh_from_db()
        assert self.comment.text == 'Updated comment text'

    def test_user_can_delete_own_comment(self):
        """Авторизованный пользователь может удалять свои комментарии"""
        self.client.force_login(self.user)
        url = reverse('news:delete', args=[self.comment.pk])
        response = self.client.post(url)
        assert response.status_code == HTTPStatus.FOUND
        assert reverse('news:detail', args=[self.news.pk]) in response.url
        assert Comment.objects.filter(pk=self.comment.pk).count() == 0

    def test_user_cannot_edit_others_comment(self):
        """
        Авторизованный пользователь не может
        редактировать чужие комментарии
        """
        self.client.force_login(self.another_user)
        url = reverse('news:edit', args=[self.comment.pk])
        edit_data = {'text': 'Hacked comment'}
        response = self.client.post(url, data=edit_data)
        assert response.status_code == HTTPStatus.NOT_FOUND
        self.comment.refresh_from_db()
        assert self.comment.text == 'Original comment'

    def test_user_cannot_delete_others_comment(self):
        """Авторизованный пользователь не может удалять чужие комментарии"""
        self.client.force_login(self.another_user)
        url = reverse('news:delete', args=[self.comment.pk])
        response = self.client.post(url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert Comment.objects.filter(pk=self.comment.pk).count() == 1
