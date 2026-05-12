import unittest
from unittest.mock import Mock, patch

from flask import Flask
import login_app


class TestLoginApp(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.mock_user_class = Mock()
        self.user_patcher = patch.object(login_app, 'User', self.mock_user_class)
        self.user_patcher.start()

    def tearDown(self):
        self.user_patcher.stop()

    def test_load_user_calls_user_objects(self):
        expected = Mock()
        self.mock_user_class.objects.return_value.first.return_value = expected
        self.assertIs(login_app.load_user(42), expected)
        self.mock_user_class.objects.assert_called_once_with(id=42)

    def test_login_returns_error_when_user_missing(self):
        with self.app.test_request_context('/login', method='POST', data={'email': 'x', 'password': 'y'}):
            self.mock_user_class.objects.return_value.first.return_value = None
            with patch.object(login_app, 'render_template', return_value='rendered') as render_template:
                self.assertEqual(login_app.login(), 'rendered')
                render_template.assert_called_once_with('login_page.html', login_error='Uživatel s touto emailovou adresou není registrován')

    def test_login_returns_error_when_password_invalid(self):
        with self.app.test_request_context('/login', method='POST', data={'email': 'x', 'password': 'wrong'}):
            user = Mock(is_active=True, get_password_hash=Mock(return_value='hash'))
            self.mock_user_class.objects.return_value.first.return_value = user
            with patch.object(login_app, 'check_password_hash', return_value=False), patch.object(login_app, 'render_template', return_value='rendered') as render_template:
                self.assertEqual(login_app.login(), 'rendered')
                render_template.assert_called_once_with('login_page.html', login_error='Nesprávné přihlašovací údaje')

    def test_login_success_redirects(self):
        with self.app.test_request_context('/login', method='POST', data={'email': 'x', 'password': 'right'}):
            user = Mock(is_active=True, get_password_hash=Mock(return_value='hash'))
            self.mock_user_class.objects.return_value.first.return_value = user
            with patch.object(login_app, 'check_password_hash', return_value=True), patch.object(login_app, 'login_user') as login_user, patch.object(login_app, 'redirect', return_value='redirected') as redirect:
                self.assertEqual(login_app.login(), 'redirected')
                login_user.assert_called_once_with(user)
                redirect.assert_called_once_with('/')

    def test_register_returns_error_for_existing_email(self):
        with self.app.test_request_context('/register', method='POST', data={'email': 'x', 'password': 'p', 'password_again': 'p'}):
            self.mock_user_class.objects.return_value.first.return_value = Mock()
            with patch.object(login_app, 'render_template', return_value='rendered') as render_template:
                self.assertEqual(login_app.register(), 'rendered')
                render_template.assert_called_once_with('registration_page.html', login_error='Uživatel s touto emailovou adresou je již zaregistrovaný')

    def test_register_returns_error_for_mismatched_passwords(self):
        with self.app.test_request_context('/register', method='POST', data={'email': 'x', 'password': 'p1', 'password_again': 'p2'}):
            self.mock_user_class.objects.return_value.first.return_value = None
            with patch.object(login_app, 'render_template', return_value='rendered') as render_template:
                self.assertEqual(login_app.register(), 'rendered')
                render_template.assert_called_once_with('registration_page.html', login_error='Zadaná hesla se neshodují')

    def test_register_success_saves_user_and_redirects(self):
        with self.app.test_request_context('/register', method='POST', data={'email': 'x', 'password': 'p', 'password_again': 'p'}):
            self.mock_user_class.objects.return_value.first.return_value = None
            mock_user_instance = Mock()
            self.mock_user_class.return_value = mock_user_instance
            with patch.object(login_app, 'generate_password_hash', return_value='hashed'), patch.object(login_app, 'login_user') as login_user, patch.object(login_app, 'redirect', return_value='redirected') as redirect:
                self.assertEqual(login_app.register(), 'redirected')
                mock_user_instance.save.assert_called_once()
                login_user.assert_called_once_with(mock_user_instance)
                redirect.assert_called_once_with('/my-pigeons')

    def test_logout_redirects_to_login(self):
        with patch.object(login_app, 'logout_user') as logout_user, patch.object(login_app, 'redirect', return_value='redirected') as redirect:
            self.assertEqual(login_app.logout(), 'redirected')
            logout_user.assert_called_once()
            redirect.assert_called_once_with('/login')
