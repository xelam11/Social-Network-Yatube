from django.test import TestCase
from django.contrib.auth import get_user_model

from posts.models import Post, Group, Comment, Follow


class ModelTest(TestCase):
    """ В данном классе расположены тесты для проверки
            работоспособности моделей"""
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
        cls.user_follower = get_user_model().objects.create(
            username="TestUser_follower")
        cls.following = Follow.objects.create(author=cls.user,
                                              user=cls.user_follower) # Правильно ли вообще создал взаимосвязь?

    def test_verbose_name_in_the_fields_is_the_same_as_expected_in_group_model(self):
        group = self.group
        field_verboses = {
            "title": "Название",
            "slug": "Адрес",
            "description": "Описание",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_in_the_fields_is_the_same_as_expected_in_post_model(self):
        post = self.post
        field_verboses = {
            "text": "Текст",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Группа",
            "image": "Изображение",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_in_the_fields_is_the_same_as_expected_in_comment_model(self):
        comment = self.comment
        field_verboses = {
            "post": "Пост",
            "author": "Автор",
            "text": "Текст",
            "created": "Дата публикации",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_in_the_fields_is_the_same_as_expected_in_follow_model(self):
        following = self.following
        field_verboses = {
            "user": "Подписчик",
            "author": "Блогер",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    following._meta.get_field(value).verbose_name, expected)

    def test_help_text_in_the_fields_is_the_same_as_expected_in_post_model(self):
        post = self.post
        field_help_texts = {
            "text": "Напишите текст",
            "group": "Выберите группу",
            "image": "Загрузите изображение",
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_help_text_in_the_fields_is_the_same_as_expected_in_comment_model(self):
        help_text = self.comment._meta.get_field('text').help_text

        self.assertEqual(help_text, "Напишите текст")

    def test_group_str_is_a_title_field(self):
        self.assertEquals(self.group.title, str(self.group))

    def test_post_str_is_a_text_field(self):
        expected_object_name = self.post.text[:15]

        self.assertEquals(expected_object_name, str(self.post))

    def test_comment_str_is_a_text_field(self):
        expected_object_name = self.comment.text[:15]

        self.assertEquals(expected_object_name, str(self.comment))
