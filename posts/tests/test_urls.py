from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from posts.models import Group, Post, Comment

User = get_user_model()


class URLTest(TestCase):
    """ В данном классе расположены тесты для проверки
            работоспособности URL"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title="Group_title",
                                         slug="Group_slug",
                                         description="Group_description")
        cls.user = get_user_model().objects.create(username="TestUser")
        cls.post = Post.objects.create(author=cls.user, text="Post_text")
        cls.comment = Comment.objects.create(author=cls.user,
                                             post=cls.post,
                                             text="Comment_text")

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_url_available_for_guest_client(self):
        url_names = (
            "/",
            f"/group/{self.group.slug}/",
            f"/{self.user.username}/",
            f"/{self.user.username}/{self.post.id}/",
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_url_available_for_authorized_client(self):
        url_names = (
            "/new/",
            f"/{self.user.username}/{self.post.id}/edit/",
            "/follow/",
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_new_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get('/new/', follow=True)

        self.assertRedirects(response, '/auth/login/?next=/new/')     # нет смысла тут его держать и другие 2?

    # def test_username_post_id_edit_guest_url_exists_at_desired_location(self):
    #     """Страница /username/post_id/edit/ доступна только автору поста.
    #     Неавторизированного пользователя перенаправит на страницу логина"""
    #     response = self.guest_client.get('/TestUser/1/edit/', follow=True)
    #     self.assertRedirects(response, '/auth/login/?next=/TestUser/1/edit/')
    #
    # def test_username_post_id_edit_not_author_url_exists_at_desired_location(
    #         self):
    #     """Страница /username/post_id/edit/ доступна только автору поста.
    #     Авторизированного пользователя, но не автора поста, перенаправит на
    #     страницу просмотра этой записи"""
    #     user_not_author = User.objects.create_user(username='not_author')
    #     self.client.force_login(user_not_author)
    #
    #     response = self.client.get('/TestUser/1/edit/', follow=True)
    #     self.assertRedirects(response, '/TestUser/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'index.html',
            '/new/': 'new_post.html',
            '/group/Group_slug/': 'group.html',
            '/TestUser/1/edit/': 'new_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_returns_404_status_code_if_url_doesnt_exist(self):
        url = f'/{get_random_string(10)}/'

        response = self.client.get(url)

        self.assertEquals(response.status_code, 404)

    @override_settings(DEBUG=False)
    def test_renders_custom_template_on_404(self):
        url = f'/{get_random_string(10)}/'

        response = self.client.get(url)

        self.assertTemplateUsed(response, "misc/404.html")

    # @override_settings(DEBUG=False)
    # def test_renders_custom_template_on_500(self):
    #     response = self.client.get('/500')
    #
    #     self.assertTemplateUsed(response, "misc/500.html")