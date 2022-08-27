from datetime import date
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post2 = Post.objects.create(
            text='Тестовый текст поста авторизованный пользователь',
            author=self.user,
            pub_date=date.today(),
            group=self.group
        )

    def test_home_and_group(self):
        """страницы доступные всем"""
        url_names = (
            '/',
            f'/group/{self.group.slug}/',
        )
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_url_for_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_for_authorized(self):
        """Страница /posts/<post_id>/edit/
        доступна авторизованному пользователю."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post2.id}/edit/': 'posts/create_post.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
        }

        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        response = self.guest_client.get('/zxcv/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
