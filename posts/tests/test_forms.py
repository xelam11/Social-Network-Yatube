import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Group, Post, Comment
from yatube.settings import MEDIA_ROOT

User = get_user_model()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostFormTests(TestCase):
    """"В данном классе расположены тесты для проверки
            создания и редактирования постов"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username="TestUser")
        cls.post = Post.objects.create(author=cls.user, text="Тестовый текст")
        cls.group = Group.objects.create(title="Тестовая группа",
                                         slug="test-slug",
                                         description="Тестовое описание группы"
                                         )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_new_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif"
        )
        form_data = {
            "text": self.post.text,
            "author": self.user,
            "group": self.group.id,
            "image": uploaded,
        }

        response = self.authorized_client.post(
            reverse("posts:new_post"),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse("posts:index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data["text"],
            author=form_data["author"],
            image=f"posts/{form_data['image'].name}",
            group=form_data["group"]).exists())

    def test_update_post(self):
        group_new = Group.objects.create(slug="test-slug-new",
                                         title="Тестовая группа новая",
                                         description="Тестовое описание новое."
                                         )
        small_gif_new = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name="small_new.gif",
            content=small_gif_new,
            content_type="image/gif"
        )

        form_data = {
            "text": "Новый текст",
            "group": group_new.id,
            "image": uploaded,
        }

        response = self.authorized_client.post(
            reverse(
                "posts:post_edit", args=[self.user.username, self.post.id]),
            data=form_data,
            follow=True,
        )
        self.post.refresh_from_db()

        self.assertRedirects(response, reverse(
            "posts:post", args=[self.user.username, self.post.id]))
        self.assertEqual(self.post.text, form_data["text"])
        self.assertEqual(self.post.group.id, form_data["group"])
        self.assertEqual(self.post.image.name,
                         f"posts/{form_data['image'].name}")


class CommentFormTests(TestCase):
    """"В данном классе расположены тесты для проверки
        создания комментария"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(author=cls.user, text='Тестовый текст')

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_create_comment(self):
        comments_count = Comment.objects.count()
        form_data = {'text': 'Текст комментария'}

        response = self.authorized_client.post(reverse(
            'posts:add_comment', kwargs={"username": self.user.username,
                                         "post_id": self.post.id}),
            data=form_data, follow=True)

        self.assertRedirects(response, reverse(
            'posts:post', kwargs={"username": self.user.username,
                                  "post_id": self.post.id}))
        self.assertTrue(
            Comment.objects.filter(text=form_data['text'],
                                   post=self.post,
                                   author=self.user).exists())
        self.assertEqual(Comment.objects.count(), comments_count + 1)
