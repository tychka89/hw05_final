from posts.forms import PostForm
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post
from django.urls import reverse
from datetime import date

import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_authorized(self):
        """Для авторизованного пользоветеля создается пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        post_1 = Post.objects.get(id=self.post.id)
        author_1 = User.objects.get(username=self.user)
        group_1 = Group.objects.get(title=self.group.title)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}))
        self.assertEqual(post_1.text, self.post.text)
        self.assertEqual(author_1.username, str(self.user))
        self.assertEqual(group_1.title, self.group.title)

    def test_create_post_anonymous(self):
        """Для неавторизованного пользоветеля пост не создается."""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_post_authorized(self):
        """Авторизованный пользователь может редактировать пост."""
        post_2 = Post.objects.get(id=self.post.id)
        self.client.get(f'/posts/{self.post.id}/edit/')
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.post.id)
        self.assertRedirects(response_edit, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response_edit.status_code, 200)
        self.assertNotEqual(post_2.text, 'Измененный текст')

    def test_edit_post_anonymous(self):
        """Неавторизованный пользователь не может редактировать пост."""
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id,
        }
        response_edit = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post_2 = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response_edit, f'/auth/login/?next=/posts/{self.post.id}/edit/')
        self.assertEqual(response_edit.status_code, 200)
        self.assertNotEqual(post_2.text, 'Измененный текст')

    def test_create_post_with_picture(self):
        count_posts = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый текст 2',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True,
        )
        post_3 = Post.objects.get(text='Тестовый текст 2')
        author_3 = User.objects.get(username=self.user)
        group_3 = Group.objects.get(title=self.group.title)
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}))
        self.assertEqual(post_3.text, 'Тестовый текст 2')
        self.assertEqual(author_3.username, str(self.user))
        self.assertEqual(group_3.title, self.group.title)
        self.assertTrue(
            Post.objects.filter(
                id=post_3.id,
                image='posts/small.gif'
            ).exists()
        )
