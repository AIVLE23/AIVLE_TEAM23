from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import ChatLog

User = get_user_model()

class ChatTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='Testpass123!',
            email='test@example.com'
        )
        self.client = Client()

    def test_chat_creation(self):
        self.client.login(username='testuser', password='Testpass123!')
        response = self.client.post('/aichat/', {'title': 'Test Chat'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ChatLog.objects.filter(title='Test Chat').exists())

    def test_chat_message_flow(self):
        chatlog = ChatLog.objects.create(user=self.user, title="Test")
        response = self.client.get(f'/aichat/{chatlog.id}/')
        self.assertEqual(response.status_code, 200)