from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from crypto.rsa import generate_keypair, serialize_public_key


class PostApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='post-author@example.com',
            username='post_author',
            password='StrongPass123!',
        )
        public_key, _ = generate_keypair(bits=256)
        self.user.public_key = serialize_public_key(public_key)
        self.user.save(update_fields=['public_key'])
        self.client.force_authenticate(user=self.user)

    def test_create_post_returns_201_and_encrypted_storage(self):
        payload = {
            'title': 'Demo title',
            'content': 'Demo content body',
        }

        response = self.client.post('/api/posts/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author'], self.user.id)
        self.assertEqual(response.data['title'], 'Encrypted title (author-only decryption)')
        self.assertEqual(response.data['content'], 'Encrypted content (author-only decryption)')
        self.assertNotEqual(response.data['title_encrypted'], payload['title'])
        self.assertNotEqual(response.data['content_encrypted'], payload['content'])

    def test_create_post_with_blank_title_returns_400(self):
        payload = {
            'title': '   ',
            'content': 'Still has content',
        }

        response = self.client.post('/api/posts/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
