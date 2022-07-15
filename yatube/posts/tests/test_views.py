from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..forms import PostForm
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
            author=cls.author,
            text='Тестовая пост 1',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.template_check = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author,)),
            ('posts:post_detail', (self.post.id,)),
        )

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

    def check_func(self, response, bol=False):
        """Вспомогательная функция для проверки корректного контекста"""
        if bol:
            self.assertEqual(
                response.context.get('post').text, 'Тестовая пост 1'
            )
        else:
            first_object = response.context['page_obj'][0]
            self.assertEqual(first_object.text, 'Тестовая пост 1')
            self.assertEqual(first_object.author.username, 'auth')
            self.assertEqual(first_object.group.title, 'Тестовая группа123')

    def test_index_pages_show_correct_context(self):
        """Проверка контекста в index"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_func(response)

    def test_group_list_pages_show_correct_context(self):
        """Проверка контекста в group_list"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', args=(self.group.slug,))
        )
        self.check_func(response)

    def test_profile_pages_show_correct_context(self):
        """Проверка контекста в profile"""
        response = self.authorized_client.get(reverse(
            'posts:profile', args=(self.user.username,))
        )
        self.check_func(response)

    #
    def test_post_detail_pages_show_correct_context(self):
        """Проверка контекста в post_detail"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'})
        )
        self.check_func(response, True)

    def test_create_edit_both_context(self):
        """Проверка контекста в create и edit"""
        context_urls = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for address, args in context_urls:
            with self.subTest(address=address):
                response = self.authorized_author.get(
                    reverse(address, args=args)
                )
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context.get('form'), PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)

    def test_post_correct_group(self):
        """Проверка что пост попадает в корректную группу."""
        post_count = Post.objects.count()
        post1 = Post.objects.create(
            author=self.author,
            text='Тестовая пост 1',
            group=self.group
        )
        group2 = Group.objects.create(
            title='Тестовая группа NEW',
            slug='test-slug-new',
            description='Тестовое описание NEW',
        )
        response1 = self.authorized_client.get(reverse(
            'posts:group_list', args=(group2.slug,))
        )
        response2 = self.authorized_client.get(reverse(
            'posts:post_detail', args=(post1.id,))
        )
        response3 = self.authorized_client.get(reverse(
            'posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(len(response1.context['page_obj']), settings.ZERO)
        self.assertEqual(post1.group.slug, self.group.slug)
        self.assertEqual(len(response3.context['page_obj']), post_count + 1)

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
        """Проверка пагинации"""
        pagin_urls = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,))
        )
        pages_units = (
            ('?page=1', settings.SORT10),
            ('?page=2', int(settings.SORT13) - int(settings.SORT10))
        )

        for address, args in pagin_urls:
            with self.subTest(address=address):
                for page, units in pages_units:
                    with self.subTest(page=page):
                        response = self.authorized_author.get(
                            reverse(address, args=args) + page
                        )
        self.assertEqual(len(response.context['page_obj']), units)
