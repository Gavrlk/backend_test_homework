import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from http import HTTPStatus

from news.models import News, Comment

User = get_user_model()


@pytest.mark.django_db
class TestRoutes:
    def setup_method(self):
        """Подготовка данных перед каждым тестом"""
        self.user = User.objects.create(username='TestUser')
        self.another_user = User.objects.create(username='AnotherUser')
        self.news = News.objects.create(
            title='Test News',
            text='Test text',
            date='2024-01-01'
        )
        self.comment = Comment.objects.create(
            news=self.news,
            author=self.user,
            text='Test comment'
        )

    def test_home_page_available_to_anonymous(self, client):
        """Главная страница доступна анонимному пользователю"""
        url = reverse('news:home')
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_news_detail_available_to_anonymous(self, client):
        """Страница отдельной новости доступна анонимному пользователю"""
        url = reverse('news:detail', args=[self.news.pk])
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_edit_comment_available_to_author(self, client):
        """Страница редактирования комментария доступна автору"""
        client.force_login(self.user)
        url = reverse('news:edit', args=[self.comment.pk])
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_delete_comment_available_to_author(self, client):
        """Страница удаления комментария доступна автору"""
        client.force_login(self.user)
        url = reverse('news:delete', args=[self.comment.pk])
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_anonymous_redirected_to_login_for_edit_comment(self, client):
        """Анонимный пользователь перенаправляется на страницу авторизации"""
        url = reverse('news:edit', args=[self.comment.pk])
        response = client.get(url)
        assert response.status_code == HTTPStatus.FOUND
        assert '/auth/login/' in response.url

    def test_anonymous_redirected_to_login_for_delete_comment(self, client):
        """Анонимный пользователь перенаправляется на страницу авторизации"""
        url = reverse('news:delete', args=[self.comment.pk])
        response = client.get(url)
        assert response.status_code == HTTPStatus.FOUND
        assert '/auth/login/' in response.url

    def test_user_cannot_edit_others_comment(self, client):
        """
        Авторизованный пользователь не может
        редактировать чужие комментарии
        """
        client.force_login(self.another_user)
        url = reverse('news:edit', args=[self.comment.pk])
        response = client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_user_cannot_delete_others_comment(self, client):
        """Авторизованный пользователь не может удалять чужие комментарии"""
        client.force_login(self.another_user)
        url = reverse('news:delete', args=[self.comment.pk])
        response = client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_auth_pages_available_to_anonymous(self, client):
        """
        Страницы регистрации, входа и
        выхода доступны анонимным пользователям
        """
        login_url = reverse('users:login')
        signup_url = reverse('users:signup')
        response_login = client.get(login_url)
        response_signup = client.get(signup_url)
        assert response_login.status_code == HTTPStatus.OK
        assert response_signup.status_code == HTTPStatus.OK
        logout_url = reverse('users:logout')
        response_logout = client.get(logout_url)
        assert response_logout.status_code in (
            [HTTPStatus.OK, HTTPStatus.FOUND, HTTPStatus.METHOD_NOT_ALLOWED]
        )
        if response_logout.status_code == HTTPStatus.METHOD_NOT_ALLOWED:
            response_logout = client.post(logout_url)
            assert response_logout.status_code in (
                [HTTPStatus.OK, HTTPStatus.FOUND]
            )
