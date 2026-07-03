from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import BlogPost


class PostTestBase(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='author', password='Sup3rS3cret!pw')
        self.other = User.objects.create_user(
            username='other', password='Sup3rS3cret!pw')
        self.post = BlogPost.objects.create(
            title='First post', content='Original content', author=self.author)

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def logout(self):
        self.client.credentials()


class PostListTests(PostTestBase):
    url = reverse('post_list')

    def test_list_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_all_posts(self):
        BlogPost.objects.create(
            title='Second', content='More', author=self.other)
        self.authenticate(self.author)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_ordered_newest_first(self):
        newer = BlogPost.objects.create(
            title='Second', content='More', author=self.author)
        self.authenticate(self.author)
        response = self.client.get(self.url)
        self.assertEqual(response.data[0]['id'], newer.id)

    def test_create_post_success(self):
        self.authenticate(self.author)
        response = self.client.post(self.url, {
            'title': 'Brand new',
            'content': 'Fresh content',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Brand new')
        # Author is taken from the token, not the request body.
        self.assertEqual(response.data['author'], 'author')
        self.assertEqual(BlogPost.objects.count(), 2)

    def test_create_ignores_author_in_body(self):
        self.authenticate(self.author)
        response = self.client.post(self.url, {
            'title': 'Spoofed',
            'content': 'Trying to set another author',
            'author': self.other.username,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author'], 'author')

    def test_create_requires_authentication(self):
        response = self.client.post(self.url, {
            'title': 'Nope',
            'content': 'Should fail',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_rejects_missing_fields(self):
        self.authenticate(self.author)
        response = self.client.post(self.url, {'title': 'No content'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)


class PostDetailTests(PostTestBase):
    def detail_url(self, pk):
        return reverse('post_detail', args=[pk])

    def test_retrieve_post_success(self):
        self.authenticate(self.other)
        response = self.client.get(self.detail_url(self.post.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.post.pk)
        self.assertEqual(response.data['author'], 'author')

    def test_retrieve_requires_authentication(self):
        response = self.client.get(self.detail_url(self.post.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_missing_post_returns_404(self):
        self.authenticate(self.author)
        response = self.client.get(self.detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_put_by_author_success(self):
        self.authenticate(self.author)
        response = self.client.put(self.detail_url(self.post.pk), {
            'title': 'Updated title',
            'content': 'Updated content',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated title')

    def test_put_by_non_author_forbidden(self):
        self.authenticate(self.other)
        response = self.client.put(self.detail_url(self.post.pk), {
            'title': 'Hijacked',
            'content': 'Nope',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'First post')

    def test_put_missing_fields_returns_400(self):
        self.authenticate(self.author)
        response = self.client.put(self.detail_url(self.post.pk), {
            'title': 'Only title',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)


    def test_patch_by_author_success(self):
        self.authenticate(self.author)
        response = self.client.patch(self.detail_url(self.post.pk), {
            'title': 'Patched title',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Patched title')
        self.assertEqual(self.post.content, 'Original content')

    def test_patch_by_non_author_forbidden(self):
        self.authenticate(self.other)
        response = self.client.patch(self.detail_url(self.post.pk), {
            'title': 'Hijacked',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_delete_by_author_success(self):
        self.authenticate(self.author)
        response = self.client.delete(self.detail_url(self.post.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_delete_by_non_author_forbidden(self):
        self.authenticate(self.other)
        response = self.client.delete(self.detail_url(self.post.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_delete_requires_authentication(self):
        response = self.client.delete(self.detail_url(self.post.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_write_on_missing_post_returns_404(self):
        self.authenticate(self.author)
        response = self.client.delete(self.detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
