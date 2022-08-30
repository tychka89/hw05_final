from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from posts.models import Group, Post, Comment, Follow
from django.urls import reverse
from django import forms
from datetime import date

import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from http import HTTPStatus


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # settings.TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            pub_date=date.today(),
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template_authorized(self):
        """URL-адрес использует соответствующий шаблон."""
        # settings.TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.post2 = Post.objects.create(
            text='Тестовый текст поста',
            author=self.user,
            pub_date=date.today(),
            group=self.group,
            image=uploaded
        )
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_posts', kwargs={'slug': self.group.slug})):
            'posts/group_list.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            (reverse('posts:post_edit', kwargs={'post_id': self.post2.id})):
            'posts/create_post.html',
            (reverse('posts:profile',
             kwargs={'username': self.user.username})):
            'posts/profile.html',
            (reverse('posts:post_detail', kwargs={'post_id': self.post2.id})):
            'posts/post_detail.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_redirect_authorized_on_profile(self):
        """Страницы перенаправят авторизированного пользователя на профайл."""
        templates_pages_names = {
            (reverse('posts:profile_follow',
             kwargs={'username': self.post.author})):
            f'/profile/{self.post.author}/',
            (reverse('posts:profile_unfollow',
             kwargs={'username': self.post.author})):
            f'/profile/{self.post.author}/',
            (reverse('posts:add_comment',
             kwargs={'post_id': self.post.id})):
            f'/posts/{self.post.id}/'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertRedirects(response, template)

    def test_pages_redirect_anonymous_on_admin_login(self):
        """Страницы перенаправят анонимного пользователя
        на страницу логина."""
        templates_pages_names = {
            reverse('posts:create_post'): '/auth/login/?next=/create/',
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id})):
            f'/auth/login/?next=/posts/{self.post.id}/edit/',
            (reverse('posts:profile_follow',
             kwargs={'username': self.post.author})):
            f'/auth/login/?next=/profile/{self.post.author}/follow/',
            (reverse('posts:profile_unfollow',
             kwargs={'username': self.post.author})):
            f'/auth/login/?next=/profile/{self.post.author}/unfollow/',
            (reverse('posts:add_comment',
             kwargs={'post_id': self.post.id})):
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertRedirects(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_pub_date_0 = first_object.pub_date
        post_group_0 = first_object.group
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_page сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_pub_date_0 = first_object.pub_date
        post_group_0 = first_object.group
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_pub_date_0 = first_object.pub_date
        post_group_0 = first_object.group
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(
            response.context.get('post').pub_date, self.post.pub_date)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(
            response.context.get(
                'number_of_posts'), self.post.author.posts.count())
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_add_comment(self):
        """Комментарий добавляется к посту."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post((
            reverse('posts:add_comment', kwargs={'post_id': self.post.id})),
            data=form_data,
            follow=True
        )
        comment_1 = Comment.objects.get(id=self.post.id)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Comment.objects.filter(
                author=self.user,
                text=form_data['text'],
            ).exists()
        )
        self.assertEqual(comment_1.text, 'Тестовый комментарий')

    def test_edit_post_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        # settings.TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.post2 = Post.objects.create(
            text='Тестовый текст поста',
            author=self.user,
            pub_date=date.today(),
            group=self.group,
            image=uploaded
        )
        response = (self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post2.id})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                _form = response.context.get('form')
                form_field = _form.fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertTrue(post_text_0, 'Тестовый текст поста2')

    def test_add_comment_authorized(self):
        comments_count = Comment.objects.count()
        my_comment = 'Комментарий'
        form_data = {
            'text': my_comment,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('comments')[0].text, my_comment)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.post = []
        for i in range(13):
            cls.post.append(Post(
                text=f'Тестовый текст поста {i}',
                author=cls.user,
                pub_date=date.today(),
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.post)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_first_page_contains_ten_records(self):
        list_urls = {
            reverse('posts:index'): 'index',
            reverse('posts:group_posts', kwargs={
                'slug': self.group.slug}): 'group',
            reverse('posts:profile', kwargs={
                'username': self.post[0].author}): 'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        list_urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse('posts:group_posts', kwargs={
                'slug': self.group.slug}) + '?page=2': 'group',
            reverse('posts:profile', kwargs={
                'username': self.post[0].author}) + '?page=2': 'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context['page_obj']), 3)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_user'),
            text='Тестовый текст поста кэш')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        state_1 = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Измененный текст кэш'
        post_1.save()
        state_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(state_1.content, state_2.content)
        cache.clear()
        state_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(state_1.content, state_3.content)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FollowTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user1')
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования подписок'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_follow(self):
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_follow_anonymous(self):
        self.guest_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_unfollow(self):
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}))
        self.client_auth_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_unfollow_anonymous(self):
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}))
        self.guest_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_author_cannt_follow_himself(self):
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_follower.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """Пост появляется в ленте подписчика."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_1 = response.context['page_obj'][0].text
        self.assertEqual(post_text_1, self.post.text)
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response, self.post.text)
