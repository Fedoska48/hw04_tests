from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()

class FirstAccess(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа123',
            slug='testslug',
            description='Тестовое описание123',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост 1',
            id='1'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = User.objects.get(username='auth')
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_urls_guest_index(self):
        """Доступность главной страницы"""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_urls_guest_group_list(self):
        """Страница /group/ доступна любому пользователю."""
        response = self.guest_client.get('/group/testslug/')
        self.assertEqual(response.status_code, 200)

    def test_urls_guest_profile(self):
        """Страница /profile/ доступна любому пользователю."""
        response = self.guest_client.get('/profile/HasNoName/')
        self.assertEqual(response.status_code, 200)

    def test_urls_guest_posts(self):
        """Страница /posts/ доступна любому пользователю."""
        response = self.guest_client.get('/posts/1/')
        self.assertEqual(response.status_code, 200)

    def test_urls_guest_fakepage(self):
        """Ответ 404 на несуществующую страницу"""
        response = self.guest_client.get('/fakepage/')
        self.assertEqual(response.status_code, 404)

    def test_urls_author_posts_edit(self):
        """Страница /create/ доступна автору поста."""
        if self.authorized_client == self.user:
            response = self.client.get('/posts/1/edit/')
            self.assertEqual(response.status_code, 200)

    def test_post_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_posts_edit_list_url_redirect_anonymous(self):
        """Страница edit перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/'
        )

    def test_create_list_url_redirect_anonymous(self):
        """Страница create перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_urls_correct_posts(self):
        """Проверка корректности шаблонов"""
        templates_urls = {
            '/': 'posts/index.html',
            '/group/testslug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html'
        }
        for address, template in templates_urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)