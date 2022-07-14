from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Group, Post
from yatube import settings

User = get_user_model()


class CorrectTemplateTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.get(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа123',
            slug='test-slug',
            description='Тестовое описание123',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост 1',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_post_detail_pages_authorized_uses_correct_template(self):
        """URL-адреса используют шаблон posts/post_detail.html."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertTemplateUsed(response, 'posts/post_detail.html')

    def test_post_create_url_exists_at_desired_location(self):
        """URL-адреса используют шаблон posts/create_post.html."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_view_author_posts_edit(self):
        """URL-адреса для автора используют шаблон posts/create_post.html."""
        if self.authorized_client == self.user:
            response = self.authorized_client.get(reverse('posts:post_edit'))
            self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_pages_show_correct_context(self):
        """Проверка контекста в index"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        self.assertEqual(post_text_0, 'Тестовая пост 1')
        self.assertEqual(post_author_0, 'auth')
        self.assertEqual(post_group_0, 'Тестовая группа123')

    def test_group_list_pages_show_correct_context(self):
        """Проверка контекста в group_list"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', args=(self.group.slug,))
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        self.assertEqual(post_text_0, 'Тестовая пост 1')
        self.assertEqual(post_author_0, 'auth')
        self.assertEqual(post_group_0, 'Тестовая группа123')

    def test_profile_pages_show_correct_context(self):
        """Проверка контекста в profile"""
        response = self.authorized_client.get(reverse(
            'posts:profile', args=(self.user.username,))
        )
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        self.assertEqual(post_author_0, 'auth')

    def test_post_detail_pages_show_correct_context(self):
        """Проверка контекста в post_detail"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(response.context.get('post').text, 'Тестовая пост 1')

    def test_create_edit_both_context(self):
        context_urls = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,))
        )
        for address, args in context_urls:
            with self.subTest(address=address):
                response = self.authorized_author.get(
                    reverse(address, args=args)
                )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.get(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа123',
            slug='test-slug',
            description='Тестовое описание123',
        )
        cls.posts = [
            Post(
                text=f'Тестовый пост {number_post}',
                author=cls.user,
                group=cls.group,
            )
            for number_post in range(settings.SORT13)
        ]
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_pagin_new(self):
        pagin_urls = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,))
        )
        pages_units = (
            ('?page=1', settings.SORT10),
            ('?page=2', 3)
        )
        for address, args in pagin_urls:
            for page, units in pages_units:
                with self.subTest(address=address, page=page):
                    response = self.authorized_author.get(
                        reverse(address, args=args) + page
                    )
                if units == settings.SORT10:
                    self.assertEqual(len(response.context['page_obj']),
                                     settings.SORT10)
                else:
                    self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_index_page_contains_ten_records(self):
        """Проверка постов на 1-й странице index."""
        response = self.authorized_author.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), settings.SORT10)

    def test_second_index_page_contains_three_records(self):
        """Проверка постов на 2-й странице index."""
        response = self.authorized_author.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_page_contains_ten_records(self):
        """Проверка постов на 1-й странице group_list."""
        response = self.authorized_author.get(reverse(
            'posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(len(response.context['page_obj']), settings.SORT10)

    def test_second_group_page_contains_three_records(self):
        """Проверка постов на 2-й странице group_list."""
        response = self.authorized_author.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_profile_page_contains_ten_records(self):
        """Проверка постов на 1-й странице profile."""
        response = self.authorized_author.get(reverse(
            'posts:profile', args=(self.user.username,))
        )
        self.assertEqual(len(response.context['page_obj']), settings.SORT10)

    def test_second_profile_page_contains_three_records(self):
        """Проверка постов на 2-й странице profile."""
        response = self.authorized_author.get(reverse(
            'posts:profile', kwargs={'username': 'auth'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_post_index_exist(self):
        """Пост есть в index."""
        self.post = Post.objects.first()
        response = self.authorized_author.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)

    def test_post_group_exist(self):
        """Пост есть в group_list."""
        response = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}))
        self.assertEqual(response.context['group'].slug, self.group.slug)

    def test_post_profile_exist(self):
        """Пост есть в profile."""
        self.post = Post.objects.first()
        response = self.authorized_author.get(reverse(
            'posts:profile', kwargs={'username': 'auth'}))
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)
