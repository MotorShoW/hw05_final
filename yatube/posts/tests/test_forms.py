import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
             )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='Name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест текст',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_form(self):
        """При отправке формы поста создается запись в БД"""
        posts_count = Post.objects.count()
        image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'image': image,
        }
        response = self.authorized_client.post(reverse(
            'posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        index_response = self.authorized_client.get(reverse('posts:index'))
        first_obj = index_response.context['page_obj'][0]
        self.assertEqual(first_obj.text, form_data['text'])
        self.assertEqual(first_obj.group, self.group)
        self.assertEqual(first_obj.author, self.user)
        self.assertEqual(first_obj.image, 'posts/small.gif')
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.user,
                group=self.group,
            ).exists()
        )

    def test_edit_post_form(self):
        """При редактировании формы поста создается запись в БД"""
        image = SimpleUploadedFile(
            name='second_small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Редактированный текст',
            'image': image,
        }
        response = self.authorized_client.post(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_edit = response.context['post']
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(post_edit.text, form_data['text'])
        self.assertEqual(post_edit.group, self.group)
        self.assertEqual(post_edit.author, self.user)
        self.assertEqual(post_edit.image, 'posts/second_small.gif')
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.user,
                group=self.group,
            ).exists()
        )


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CommentForm()
        cls.user = User.objects.create_user(username='Name')
        cls.post = Post.objects.create(
            text='Тестовый Комментарий',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment_authorized(self):
        self.assertEqual(self.post.comments.count(), 0)
        form_data = {'text': 'Тестовый Комментарий'}
        response = self.authorized_client.post(reverse(
            'posts:add_comment', kwargs={
                'post_id': self.post.id,
            }),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(self.post.comments.count(), 1)
        comment = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        first_object = comment.context['comments'][0]
        self.assertEqual(first_object.text, 'Тестовый Комментарий')
        self.assertEqual(first_object.author, self.user)

    def test_add_comment_unauthorized(self):
        self.assertEqual(self.post.comments.count(), 0)
        form_data = {'text': 'Тестовый Комментарий'}
        response = self.guest_client.post(reverse(
            'posts:add_comment', kwargs={
                'post_id': self.post.id,
            }),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        comment = reverse('posts:add_comment', kwargs={
            'post_id': self.post.id,
        })
        login = reverse('login')
        redirect = login + '?next=' + comment
        self.assertRedirects(response, redirect)
        self.assertEqual(self.post.comments.count(), 0)
