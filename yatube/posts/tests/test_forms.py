from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.form_data = {
            'text': 'New post',
            'group': cls.group.id,
        }

    def setUp(cls):
        cls.author = User.objects.create_user(username='auth')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

    def test_create_form(self):
        """Тест формы создания поста."""
        post_count = Post.objects.count()
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        post = Post.objects.all()[0]
        self.assertRedirects(
            response,
            (reverse(
                'posts:profile', kwargs={'username': self.author.username})
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(post.text, self.form_data['text'])
        self.assertEqual(post.group.id, self.form_data['group'])

    def test_edit_form(self):
        """Тест формы изменения поста."""
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        post_count = Post.objects.count()
        edit_form_data = {
            'text': 'Исправленный пост',
        }
        post = Post.objects.all()[0]
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=edit_form_data,
            follow=True
        )
        post = Post.objects.all()[0]
        self.assertRedirects(
            response,
            (reverse(
                'posts:post_detail',kwargs={'post_id': post.id})
            )
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post.text, edit_form_data['text'])
