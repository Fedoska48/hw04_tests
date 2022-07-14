from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class FirstAccess(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.get(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа123',
            slug='testslug',
            description='Тестовое описание123',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост 1',
        )

    def setUp(self):
        self.user = User.objects.create_user(username='john')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_guest_access(self):
        """Доступность для гостя."""
        urls_template = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author,)),
            ('posts:post_detail', (self.post.id,)),
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,))
        )
        for address, args in urls_template:
            with self.subTest(address=address):
                response = self.client.get(reverse(address, args=args))
                if address == 'posts:post_create' or (address
                                                      == 'posts:post_edit'):
                    self.assertEqual(
                        response.status_code, 302
                    )
                else:
                    self.assertEqual(response.status_code, 200)

    def test_user_access(self):
        """Доступность для пользователя."""
        urls_template = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author,)),
            ('posts:post_detail', (self.post.id,)),
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,))
        )
        for address, args in urls_template:
            with self.subTest(address=address):
                response = self.authorized_client.get(
                    reverse(address, args=args)
                )
                if address == 'posts:post_edit':
                    self.assertEqual(
                        response.status_code, 302
                    )
                else:
                    self.assertEqual(response.status_code, 200)

    def test_author_access(self):
        """Доступность для автора."""
        urls_template = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author,)),
            ('posts:post_detail', (self.post.id,)),
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,))
        )
        for address, args in urls_template:
            with self.subTest(address=address):
                response = self.authorized_author.get(
                    reverse(address, args=args)
                )
                self.assertEqual(response.status_code, 200)

    def test_urls_guest_fakepage(self):
        """Ответ 404 на несуществующую страницу"""
        response = self.client.get('/fakepage/')
        self.assertEqual(response.status_code, 404)

    def test_urls_correct_templates(self):
        """Проверка корректности шаблонов"""
        templates_urls = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.author,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html')
        )
        for address, args, template in templates_urls:
            with self.subTest(address=address):
                response = self.authorized_author.get(
                    reverse(address, args=args)
                )
                self.assertTemplateUsed(response, template)

    def test_reverse_urls_correct(self):
        """Проверка доступнотси автору"""
        reverse_urls = (
            ('posts:index', None, '/'),
            ('posts:group_list', ('testslug',), '/group/testslug/'),
            ('posts:profile', ('auth',), '/profile/auth/'),
            ('posts:post_detail', ('1',), '/posts/1/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit', ('1',), '/posts/1/edit/')
        )
        for address, args, links in reverse_urls:
            with self.subTest(address=address):
                response1 = self.authorized_author.get(
                    reverse(address, args=args)
                )
                response2 = self.authorized_author.get(links)
                self.assertEqual(response1.request, response2.request)
