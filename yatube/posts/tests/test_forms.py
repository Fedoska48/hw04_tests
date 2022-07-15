from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовое название',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая пост1234',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_create_form(self):
        """Тест формы создания поста."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'New post',
            'group': self.group.id,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    args=(self.author.username,)))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.author)

    def test_edit_form(self):
        self.group_2 = Group.objects.create(
            title='Тестовое название2',
            description='Тестовое описание2',
            slug='test-slug2',
        )
        post_count = Post.objects.count()
        edit_form_data = {
            'text': 'Исправленный пост',
            'group': self.group_2.id
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=edit_form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': post.id}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post.text, edit_form_data['text'])
        self.assertEqual(post.group, self.group_2)
        self.assertEqual(post.author, self.author)
        response = self.authorized_author.post(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), post_count - 1)

    def test_anonymous_create_post(self):
        """Создание поста анонимом."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'New post ANON',
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
        self.assertNotEqual(post.text, form_data['text'])
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), post_count)
