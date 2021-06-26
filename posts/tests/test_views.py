import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, SimpleTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.core.cache import cache
from django.core.paginator import Paginator

from posts.models import Group, Post, Comment, Follow

User = get_user_model()


class PagesViewTests(TestCase):
    """
    В данном классе расположены тесты, связанные с проверкой корректности:
    - шаблонов;
    - констекстов;
    - редиректов неавторизированных пользователей.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username="TestUser")
        cls.group = Group.objects.create(title="Тестовая группа",
                                         slug="test-slug",
                                         description="Тестовое описание группы"
                                         )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=cls.small_gif,
            content_type="image/gif"
        )

        cls.post = Post.objects.create(author=cls.user, text="Тестовый текст",
                                       group=cls.group, image=uploaded)
        cls.comment = Comment.objects.create(author=cls.user,
                                             post=cls.post,
                                             text="Текст комментария")

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_page_uses_correct_template(self):
        page_template_names = {
            reverse("posts:index"): "index.html",
            reverse("posts:follow_index"): "follow.html",
            reverse("posts:group",
                    kwargs={"slug": self.group.slug}): "group.html",
            reverse("posts:profile",
                    kwargs={"username": self.user.username}): "profile.html",
            reverse("posts:post",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}): "post.html",
            reverse("posts:new_post"): "new_post.html",
            reverse("posts:post_edit",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}): "new_post.html",
            reverse("posts:add_comment",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}): "post.html",
        }

        for reverse_name, template in page_template_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.post(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_add_comment_page_shows_correct_context(self):
        response = self.authorized_client.post(
            reverse("posts:add_comment",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}))

        first_post = response.context.get("post")

        self.assertEqual(first_post, self.post)

    def test_index_page_shows_correct_context(self):
        response = self.guest_client.get(reverse("posts:index"))

        first_post = response.context.get("page")[0]
        paginator = response.context.get("paginator")

        self.assertEqual(first_post, self.post)
        self.assertIsNotNone(paginator)
        self.assertIsInstance(paginator, Paginator)

    def test_follow_index_page_shows_correct_context(self):
        user_author = User.objects.create_user(username="TestUser_author")
        post_author = Post.objects.create(author=user_author,
                                          text="Тестовый текст автора")

        Follow.objects.create(user=self.user, author=user_author)

        response = self.authorized_client.get(reverse("posts:follow_index"))

        first_post = response.context.get("page")[0]
        paginator = response.context.get("paginator")

        self.assertEqual(first_post, post_author)
        self.assertIsNotNone(paginator)
        self.assertIsInstance(paginator, Paginator)

    def test_group_page_shows_correct_context(self):
        response = self.guest_client.get(
            reverse("posts:group", kwargs={"slug": self.group.slug}))

        first_post = response.context.get("page")[0]
        group = response.context.get("group")
        paginator = response.context.get("paginator")

        self.assertEqual(first_post, self.post)
        self.assertEqual(group, self.group)
        self.assertIsNotNone(paginator)
        self.assertIsInstance(paginator, Paginator)

    def test_profile_page_shows_correct_context(self):
        response = self.guest_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username}))

        first_post = response.context.get("page")[0]
        author = response.context.get("author")
        paginator = response.context.get("paginator")
        following = response.context.get("following")

        self.assertEqual(first_post, self.post)
        self.assertEqual(author, self.user)
        self.assertIsNotNone(paginator)
        self.assertIsInstance(paginator, Paginator)
        self.assertIsNotNone(following)

    def test_post_page_shows_correct_context(self):
        response = self.guest_client.get(reverse(
            "posts:post", kwargs={"username": self.user.username,
                                  "post_id": self.post.id}))

        post = response.context.get("post")
        comments = response.context.get("comments")
        author = response.context.get("author")
        form = response.context.get("form")

        self.assertEqual(post, self.post)
        self.assertQuerysetEqual(comments, Comment.objects.all(),
                                 transform=lambda x: x)
        self.assertEqual(author, self.post.author)
        self.assertIsNotNone(form)

    def test_new_post_page_shows_correct_context(self):
        response = self.authorized_client.get(reverse("posts:new_post"))

        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"username": self.user.username,
                                               "post_id": self.post.id}))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_follow_index_page_redirect_guest_client_on_login_page(self):
        response = self.guest_client.get(reverse("posts:follow_index"),
                                         follow=True)

        self.assertRedirects(response, settings.LOGIN_URL + '?next=' +
                                       reverse("posts:follow_index"))

    def test_new_post_page_redirect_guest_client_on_login_page(self):
        response = self.guest_client.get(reverse("posts:new_post"),
                                         follow=True)

        self.assertRedirects(response, '/auth/login/?next=' +
                             reverse("posts:new_post"))

    def test_post_edit_page_redirect_guest_client_on_login_page(self):
        response = self.guest_client.get(
            reverse("posts:post_edit",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}), follow=True)

        self.assertRedirects(
            response, '/auth/login/?next=' +
                      reverse("posts:post_edit",
                              kwargs={"username": self.user.username,
                                      "post_id": self.post.id}))

    def test_post_delete_page_redirect_guest_client_on_login_page(self):
        response = self.guest_client.get(
            reverse("posts:post_delete",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}), follow=True)

        self.assertRedirects(
            response, '/auth/login/?next=' +
                      reverse("posts:post_delete",
                              kwargs={"username": self.user.username,
                                      "post_id": self.post.id}))

    def test_add_comment_page_redirect_guest_client_on_login_page(self):
        response = self.guest_client.get(
            reverse("posts:add_comment",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}), follow=True)

        self.assertRedirects(response, '/auth/login/?next=' +
                             reverse("posts:add_comment",
                                     kwargs={"username": self.user.username,
                                             "post_id": self.post.id}))

    def test_profile_follow_page_redirect_guest_client_on_login_page(self):
        response = self.guest_client.get(
            reverse("posts:profile_follow",
                    kwargs={"username": self.user.username}), follow=True)

        self.assertRedirects(response, '/auth/login/?next=' +
                             reverse("posts:profile_follow",
                                     kwargs={"username": self.user.username}))

    def test_profile_unfollow_page_redirect_guest_client_on_login_page(self):
        response = self.guest_client.get(
            reverse("posts:profile_unfollow",
                    kwargs={"username": self.user.username}), follow=True)

        self.assertRedirects(response, '/auth/login/?next=' +
                             reverse("posts:profile_unfollow",
                                     kwargs={"username": self.user.username}))


class PostGroupViewTests(TestCase):
    """ В данном классе расположены тесты для проверки
        работоспособности классов Post и Group"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()
        cls.user = User.objects.create_user(username="TestUser")
        cls.group = Group.objects.create(title="Тестовая группа",
                                         slug="test-slug",
                                         description="Тестовое описание группы"
                                         )

        cls.post = Post.objects.create(author=cls.user,
                                       text="Тестовый текст",
                                       group=cls.group)

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def tearDown(self):
        cache.clear()

    def test_index_page_contains_post_if_post_has_no_group(self):
        print(Post.objects.count())

        post = Post.objects.create(author=self.user, text="Новый текст")

        print(Post.objects.count())

        response = self.guest_client.get(reverse("posts:index"))

        self.assertContains(response, self.post)
        self.assertContains(response, post)

    def test_index_page_contains_post_if_post_has_group(self):
        response = self.guest_client.get(reverse("posts:index"))

        self.assertContains(response, self.post)

    def test_index_page_has_cache(self):
        response_1 = self.guest_client.get(reverse('posts:index'))
        first_post_1 = response_1.context.get('page')[0]
        self.assertContains(response_1, first_post_1)

        Post.objects.create(author=self.user, text='Новый тестовый текст')
        response_2 = self.guest_client.get(reverse('posts:index'))
        first_post_2 = response_2.context.get('page')[0]
        self.assertNotContains(response_2, first_post_2)

        cache.clear()
        response_3 = self.guest_client.get(reverse('posts:index'))
        self.assertContains(response_3, first_post_2)

    def test_group_page_cant_be_found_if_group_was_not_created_before(self):
        response = self.guest_client.get(
            reverse("posts:group", kwargs={"slug": "some-random-slug"}))

        self.assertEquals(response.status_code, 404)

    def test_group_page_contains_post_if_post_has_group(self):
        response = self.guest_client.get(
            reverse("posts:group", kwargs={'slug': self.post.group.slug}))

        self.assertContains(response, self.post)

    def test_post_has_correct_group(self):
        group_new = Group.objects.create(title='Новая группа',
                                         slug='test-slug-new',
                                         description='Описание новой группы')

        self.assertIn(self.post, self.group.posts.all())
        self.assertNotIn(self.post, group_new.posts.all())

    def test_profile_page_cant_be_found_if_author_was_not_created_before(self):
        response = self.guest_client.get(
            reverse("posts:profile",
                    kwargs={"username": "some random username"}))

        self.assertEquals(response.status_code, 404)

    def test_profile_page_contains_post_of_author_who_created_it(self):
        response = self.guest_client.get(
            reverse("posts:profile",
                    kwargs={"username": self.user.username}))

        self.assertContains(response, self.post)

    def test_profile_page_not_contains_post_of_author_who_not_created_it(self):
        user_new = User.objects.create_user(username="TestUser_new")
        post_new = Post.objects.create(author=user_new, text="Текст")

        response = self.guest_client.get(
            reverse("posts:profile",
                    kwargs={"username": self.user.username}))

        self.assertNotContains(response, post_new)

    def test_post_page_cant_be_found_if_user_was_not_created_before(self):
        response = self.guest_client.get(
            reverse("posts:post",
                    kwargs={"username": "some random username",
                            "post_id": self.post.id}))

        self.assertEquals(response.status_code, 404)

    def test_post_page_cant_be_found_if_post_was_not_created_before(self):
        response = self.guest_client.get(
            reverse("posts:post",
                    kwargs={"username": self.user.username,
                            "post_id": 13}))

        self.assertEquals(response.status_code, 404)

    def test_post_delete_page_cant_be_found_if_post_was_not_created_before(self):
        response = self.authorized_client.post(
            reverse("posts:post_delete",
                    kwargs={"username": self.user.username,
                            "post_id": 13}))

        self.assertEquals(response.status_code, 404)

    def test_post_delete_page_cant_be_found_if_user_was_not_created_before(self):
        response = self.authorized_client.post(
            reverse("posts:post_delete",
                    kwargs={"username": "some random username",
                            "post_id": self.post.id}))

        self.assertEquals(response.status_code, 404)

    def test_not_author_of_the_post_cant_correct_it(self):
        user_new = User.objects.create_user(username="TestUser_new")
        post_new = Post.objects.create(author=user_new, text="Текст")

        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"username": user_new.username,
                                               "post_id": post_new.id}))

        self.assertRedirects(response,
                             reverse("posts:post",
                                     kwargs={"username": user_new.username,
                                             "post_id": post_new.id}))

    def test_not_author_of_the_post_cant_delete_it(self):
        user_new = User.objects.create_user(username="TestUser_new")
        post_new = Post.objects.create(author=user_new, text="Текст")

        response = self.authorized_client.get(
            reverse("posts:post_delete", kwargs={"username": user_new.username,
                                                 "post_id": post_new.id}))

        self.assertRedirects(response,
                             reverse("posts:post",
                                     kwargs={"username": user_new.username,
                                             "post_id": post_new.id}))

    def test_author_of_the_post_can_delete_it(self):
        posts_count = Post.objects.count()

        response = self.authorized_client.get(
            reverse("posts:post_delete",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}))

        self.assertEqual(Post.objects.count(), posts_count - 1)
        self.assertRedirects(response,
                             reverse("posts:profile",
                                     kwargs={"username": self.user.username}))


class CommentViewsTest(TestCase):
    """ В данном классе расположены тесты для проверки
            работоспособности класса Comment"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="TestUser")
        cls.post = Post.objects.create(author=cls.user, text="Тестовый текст")
        cls.comment = Comment.objects.create(author=cls.user,
                                             post=cls.post,
                                             text="Текст комментария")

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_add_comment_page_cant_be_found_if_get_request(self):
        response = self.authorized_client.get(
            reverse("posts:add_comment",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}))

        self.assertEquals(response.status_code, 405)

    def test_add_comment_page_cant_be_found_if_author_was_not_created_before(self):
        response = self.authorized_client.post(
            reverse("posts:add_comment",
                    kwargs={"username": "some-random-name",
                            "post_id": self.post.id}))

        self.assertEquals(response.status_code, 404)

    def test_add_comment_page_cant_be_found_if_post_was_not_created_before(self):
        response = self.authorized_client.post(
            reverse("posts:add_comment",
                    kwargs={"username": self.user.username,
                            "post_id": 13}))

        self.assertEquals(response.status_code, 404)


class FollowViewsTests(TestCase):
    """ В данном классе расположены тесты для проверки
            работоспособности класса Follow"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(
            username="TestUser_follower")
        cls.user_author = User.objects.create_user(
            username="TestUser_author")
        cls.post = Post.objects.create(author=cls.user_author,
                                       text="Тестовый текст",)

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_follower)

    def test_profile_follow_page_cant_be_found_if_author_was_not_created_before(self):
        response = self.authorized_client.get(
            reverse("posts:profile_follow",
                    kwargs={"username": "some-random-name"}))

        self.assertEquals(response.status_code, 404)

    def test_profile_unfollow_page_cant_be_found_if_author_was_not_created_before(self):
        response = self.authorized_client.get(
            reverse("posts:profile_follow",
                    kwargs={"username": "some-random-name"}))

        self.assertEquals(response.status_code, 404)

    def test_authorized_client_can_follow_for_another_user(self):
        response = self.authorized_client.get(
            reverse(
                "posts:profile_follow", args=[self.user_author.username]))

        self.assertRedirects(response, reverse(
            "posts:profile", args=[self.user_author.username]))
        self.assertTrue(self.user_author.following.filter(
            user=self.user_follower).exists())

    def test_authorized_client_can_not_follow_twice_for_one_another_user(self):
        self.user_author.following.create(user=self.user_follower)
        count_follow_1 = Follow.objects.count()

        self.authorized_client.get(reverse(
            "posts:profile_follow",
            kwargs={"username": self.user_author.username}))
        count_follow_2 = Follow.objects.count()

        self.assertEqual(count_follow_1, count_follow_2)

    def test_authorized_client_can_not_follow_for_himself(self):
        response = self.authorized_client.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.user_follower.username}))

        self.assertRedirects(response, reverse(
            "posts:profile", kwargs={"username": self.user_follower.username})) # Вот же этот тест, в чем проблема??? coverage

    def test_authorized_client_can_unfollow(self):
        self.user_author.following.create(user=self.user_follower)

        response = self.authorized_client.get(
            reverse("posts:profile_unfollow",
                    kwargs={"username": self.user_author.username}))

        self.assertRedirects(response, reverse(
            "posts:profile", args=[self.user_author.username]))
        self.assertFalse(Follow.objects.filter(
            user=self.user_follower).exists())

    def test_post_appears_for_followers_at_follow_index_page(self):
        self.user_author.following.create(user=self.user_follower)

        response = self.authorized_client.get(reverse('posts:follow_index'))

        self.assertContains(response, self.post)

    def test_post_not_appears_for_not_followers_at_follow_index_page(self):
        user_another_author = User.objects.create_user(
            username='TestUser_another_author')
        post_of_another_author = Post.objects.create(
            author=user_another_author, text='Text of another author')

        response = self.authorized_client.get(reverse('posts:follow_index'))

        self.assertNotContains(response, post_of_another_author)


class PaginatorViewsTest(TestCase):
    """ В данном классе расположены тесты для проверки
        работоспособности паджинатора"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = get_user_model().objects.create(username='User')
        for i in range(13):
            Post.objects.create(author=cls.user, text=f'Текст{i}')

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))

        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')

        self.assertEqual(len(response.context.get('page').object_list), 3)
