from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SomeUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест текст' * 10,
        )

    def test_models_have_correct_object_names(self):
        """Тестирование правильного вывода __str__"""
        expected_group_name = self.group.title
        self.assertEqual(expected_group_name, str(self.group))
        expected_post_name = self.post.text[:15]
        self.assertEqual(expected_post_name, str(self.post))
