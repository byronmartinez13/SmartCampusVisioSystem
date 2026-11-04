import re
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        self.password = "Campus-Example!826"
        self.user = User.objects.create_user(email="member@example.edu", name="Test Member", password=self.password)

    def post(self, path, data=None):
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        return self.client.post(f"/api/auth/{path}/", data or {}, format="json", HTTP_X_CSRFTOKEN=token)

    def login(self):
        return self.post("login", {"email": self.user.email, "password": self.password})

    def test_anonymous_cannot_access_dashboard_or_profile(self):
        self.assertEqual(self.client.get("/api/dashboard/").status_code, 403)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)

    def test_login_requires_csrf_even_for_anonymous_user(self):
        response = self.client.post("/api/auth/login/", {"email": self.user.email, "password": self.password})
        self.assertEqual(response.status_code, 403)

    def test_registration_hashes_password_and_cannot_escalate_role(self):
        response = self.post("register", {
            "name": "Nuevo Usuario", "email": "NEW@EXAMPLE.EDU", "password": self.password,
            "role": "admin", "is_superuser": True, "is_staff": True,
        })
        self.assertEqual(response.status_code, 201)
        created = User.objects.get(email="new@example.edu")
        self.assertTrue(created.check_password(self.password))
        self.assertNotEqual(created.password, self.password)
        self.assertEqual(created.role, "viewer")
        self.assertFalse(created.is_staff)
        self.assertFalse(created.is_superuser)
        self.assertNotIn("password", response.json())
        self.assertEqual(self.client.get("/api/auth/me/").json()["id"], created.pk)

    def test_duplicate_email_case_insensitive(self):
        response = self.post("register", {"name": "Duplicate", "email": "MEMBER@EXAMPLE.EDU", "password": self.password})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_weak_password_rejected(self):
        response = self.post("register", {"name": "Weak", "email": "weak@example.edu", "password": "1234567890"})
        self.assertEqual(response.status_code, 400)

    def test_session_persists_across_clients_then_logout_invalidates_cookie(self):
        self.assertEqual(self.login().status_code, 200)
        other = APIClient()
        other.cookies = self.client.cookies.copy()
        self.assertEqual(other.get("/api/auth/me/").json()["email"], self.user.email)
        self.assertEqual(self.post("logout").status_code, 204)
        self.assertEqual(other.get("/api/dashboard/").status_code, 403)

    def test_invalid_credentials_and_inactive_users_rejected(self):
        self.assertEqual(self.post("login", {"email": self.user.email, "password": "bad"}).status_code, 400)
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login().status_code, 400)

    def test_roles_enforced_on_server(self):
        self.login()
        self.assertEqual(self.client.get("/api/auth/users/").status_code, 403)
        self.user.role = "coordinator"
        self.user.save()
        self.assertEqual(self.client.get("/api/auth/users/").status_code, 403)
        self.user.role = "admin"
        self.user.save()
        self.assertEqual(self.client.get("/api/auth/users/").status_code, 200)

    def test_profile_change_cannot_change_role(self):
        self.login()
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        response = self.client.patch("/api/auth/me/", {"name": "Updated", "role": "admin"},
                                     format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated")
        self.assertEqual(self.user.role, "viewer")

    def test_recovery_returns_same_response_for_missing_user(self):
        actual = self.post("password/recover", {"email": self.user.email})
        absent = self.post("password/recover", {"email": "absent@example.edu"})
        self.assertEqual(actual.json(), absent.json())
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_token_single_use_and_old_session_invalidated(self):
        self.login()
        other = APIClient()
        other.force_login(self.user)
        self.post("password/recover", {"email": self.user.email})
        uid, token = re.search(r"uid=([^&\s]+)&token=([^\s]+)", mail.outbox[0].body).groups()
        self.post("logout")
        payload = {"uid": uid, "token": token, "password": "Changed-Example!927"}
        self.assertEqual(self.post("password/reset", payload).status_code, 200)
        self.assertEqual(other.get("/api/auth/me/").status_code, 403)
        self.assertEqual(self.post("password/reset", payload).status_code, 400)
        self.assertEqual(self.login().status_code, 400)
        self.assertEqual(self.post("login", {"email": self.user.email, "password": payload["password"]}).status_code, 200)

    def test_invalid_and_expired_tokens_rejected(self):
        self.assertEqual(self.post("password/reset", {"uid": "invalid", "token": "bad", "password": self.password}).status_code, 400)
        self.post("password/recover", {"email": self.user.email})
        uid, token = re.search(r"uid=([^&\s]+)&token=([^\s]+)", mail.outbox[0].body).groups()
        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            self.assertEqual(self.post("password/reset", {"uid": uid, "token": token, "password": self.password}).status_code, 400)

    def test_password_change_keeps_current_session_revokes_other(self):
        self.login()
        other = APIClient()
        other.force_login(self.user)
        self.assertEqual(self.post("password/change", {"current_password": "wrong", "password": "Other-Secret!123"}).status_code, 400)
        response = self.post("password/change", {"current_password": self.password, "password": "Other-Secret!123"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(other.get("/api/auth/me/").status_code, 403)

    def test_login_rate_limit(self):
        for _ in range(10):
            self.post("login", {"email": "absent@example.edu", "password": "bad"})
        self.assertEqual(self.post("login", {"email": "absent@example.edu", "password": "bad"}).status_code, 429)

    def test_account_without_initial_password_can_be_activated(self):
        invited = User.objects.create_user(email="invited@example.edu", name="Invited", role="admin")
        self.assertFalse(invited.has_usable_password())
        self.post("password/recover", {"email": invited.email})
        uid, token = re.search(r"uid=([^&\s]+)&token=([^\s]+)", mail.outbox[0].body).groups()
        payload = {"uid": uid, "token": token, "password": "New-Invited!347"}
        self.assertEqual(self.post("password/reset", payload).status_code, 200)
        response = self.post("login", {"email": invited.email, "password": payload["password"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "admin")
