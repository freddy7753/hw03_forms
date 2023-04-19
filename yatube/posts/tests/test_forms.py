import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

ONE_POST: int = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.form = PostForm()
        cls.posts_count = Post.objects.count()
        cls.form_data = {
            'text': 'Test post',
            'group': ''
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка на создание нового поста"""
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        post_id = Post.objects.order_by('-pub_date')[0].id
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'pk': post_id}
        ))
        self.assertEqual(
            Post.objects.count(),
            self.posts_count + ONE_POST
        )
        self.assertEqual(response.context['post'].text, 'Test post')
        self.assertEqual(response.context['post'].group, None)
        self.assertEqual(response.context['post'].author, self.user)

    def test_create_post_is_forbidden_for_guest_client(self):
        """Незарегистрированный пользователь не может создать пост"""
        self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), self.posts_count)

    def test_for_redact_post(self):
        """Тест на редактирование поста"""
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        self.new_post = Post.objects.create(
            text='Test',
            group=self.group,
            author=self.user
        )
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.new_post.id}
            ),
            data=self.form_data,
            follow=True
        )
        post_id = Post.objects.order_by('-pub_date')[0].id
        post = Post.objects.get(pk=post_id)
        self.assertEqual(post.text, 'Test post')
        self.assertEqual(post.group, None)
        self.assertEqual(post.author, self.user)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
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
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'auth'})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text='Тестовый пост',
                author=self.user,
                image='posts/small.gif'
            ).exists()
        )

    # def test_image_post(self):
    #     """При выводе поста с картинкой изображение передаётся в словаре"""
    #     small_gif = (
    #         b'\x47\x49\x46\x38\x39\x61\x02\x00'
    #         b'\x01\x00\x80\x00\x00\x00\x00\x00'
    #         b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    #         b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    #         b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    #         b'\x0A\x00\x3B'
    #     )
    #     uploaded = SimpleUploadedFile(
    #         name='small.gif',
    #         content=small_gif,
    #         content_type='image/gif'
    #     )
    #     list_pages_names = (
    #         reverse('posts:index'),
    #         reverse('posts:post_detail',
    #                 kwargs={'post_id': '2'}),
    #         reverse('posts:profile', kwargs={'username': 'auth'}),
    #         reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
    #     )
    #     for page in list_pages_names:
    #         with self.subTest(page=page):
    #             response = self.authorized_client.get(page)
    #             first_object = response.context['page_obj'][0]
    #             self.assertEqual(first_object.image, uploaded)
