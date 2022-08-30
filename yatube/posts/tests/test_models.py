from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

number_of_elements: int = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста - очень длинный',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый текст для комментария',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        models = {
            PostModelTest.post: PostModelTest.post.text[:number_of_elements],
            PostModelTest.group: PostModelTest.group.title,
            PostModelTest.comment: PostModelTest.comment.text,
            PostModelTest.follow: PostModelTest.follow.user.username
        }
        for model, expected_value in models.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), str(expected_value))

    # Я сделала проверку для модели Follow, но не поняла, зачем она нужна(
    # То есть я просто сделала что-то по аналогии
    #  и не уверена, что это вообще имеет смысл
