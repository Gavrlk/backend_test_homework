import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client
from datetime import datetime, timedelta

from news.models import News, Comment

User = get_user_model()


@pytest.mark.django_db
class TestContent:
    def setup_method(self):
        """Подготовка данных перед каждым тестом"""
        self.user = User.objects.create(username='TestUser')
        self.client = Client()
        self.news_list = []
        for i in range(12):
            news = News.objects.create(
                title=f'News {i}',
                text=f'Text {i}',
                date=datetime.today() - timedelta(days=i)
            )
            self.news_list.append(news)
        self.comments = []
        for i in range(5):
            comment = Comment.objects.create(
                news=self.news_list[0],
                author=self.user,
                text=f'Comment {i}',
                created=datetime.now() + timedelta(minutes=i)
            )
            self.comments.append(comment)

    def test_news_count_on_home_page_not_more_than_10(self):
        """Количество новостей на главной странице - не более 10"""
        url = reverse('news:home')
        response = self.client.get(url)
        assert len(response.context['object_list']) <= 10
        assert len(response.context['object_list']) == 10  # Так как создали 12

    def test_news_ordered_by_date_descending(self):
        """Новости отсортированы от самой свежей к самой старой"""
        url = reverse('news:home')
        response = self.client.get(url)
        news_list = response.context['object_list']
        dates = [news.date for news in news_list]
        assert dates == sorted(dates, reverse=True)

    def test_comments_ordered_by_created_ascending(self):
        """Комментарии отсортированы в хронологическом порядке"""
        url = reverse('news:detail', args=[self.news_list[0].pk])
        response = self.client.get(url)
        comments = response.context['news'].comment_set.all()
        created_dates = [comment.created for comment in comments]
        assert created_dates == sorted(created_dates)

    def test_comment_form_not_visible_to_anonymous(self):
        """Анонимному пользователю недоступна форма для отправки комментария"""
        url = reverse('news:detail', args=[self.news_list[0].pk])
        response = self.client.get(url)
        assert 'form' not in response.context

    def test_comment_form_visible_to_authenticated(self):
        """
        Авторизованному пользователю доступна
        форма для отправки комментария
        """
        self.client.force_login(self.user)
        url = reverse('news:detail', args=[self.news_list[0].pk])
        response = self.client.get(url)
        assert 'form' in response.context
        assert response.context['form'] is not None
