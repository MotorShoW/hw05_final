from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Name')
        cls.wrong_user = User.objects.create_user(username='WrongUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест текст'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.wrong_authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.wrong_authorized_client.force_login(self.wrong_user)
        cache.clear()

    def test_urls_exists_at_desired_location(self):
        """Проверка работоспособности URL"""
        url_names = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.id}/',
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_post_id_authorized_author_url(self):
        """Проверка доступа автора на редактирование поста"""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_create_url_authorized(self):
        """Проверка доступа авторизованного пользователя к созданию поста"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_create_url_unauthorized(self):
        """Проверка доступа неавторизованного пользователя к созданию поста"""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, 302)

    def test_edit_url_unauthorized(self):
        """Проверка доступа неавторизованного пользователя
         к редактированию поста"""
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_edit_url_not_by_author(self):
        """Проверка доступа НЕ автора к редактированию поста"""
        response = self.wrong_authorized_client.get(
            f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_unexisting_url(self):
        """Проверка несуществующей страницы на 404"""
        response = self.guest_client.get('/unexisting/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_templates(self):
        """Проверка использования правильных шаблонов"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
