from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import LoginAttemptBucket, ValidationTask, DocumentRequest
from .composition import AgentForm
from .composition_schema import SERVICES


class SecurityControlTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('ops-control',password='Test-SIGDA-2026!')
        self.user.groups.add(Group.objects.get_or_create(name='SIGDA_OPS')[0])

    def test_login_throttles_before_authentication_and_expires(self):
        for _ in range(5):
            self.assertEqual(self.client.post(reverse('login'),{'username':self.user.username,'password':'wrong'}).status_code,200)
        with patch('django.contrib.auth.forms.authenticate') as authenticate:
            response=self.client.post(reverse('login'),{'username':self.user.username,'password':'Test-SIGDA-2026!'})
            self.assertEqual(response.status_code,429);authenticate.assert_not_called()
        self.assertEqual(response['Retry-After'],'900')
        LoginAttemptBucket.objects.update(started_at=timezone.now()-timedelta(minutes=16))
        self.assertEqual(self.client.post(reverse('login'),{'username':self.user.username,'password':'Test-SIGDA-2026!'}).status_code,302)
        self.assertNotIn(self.user.username,str(list(LoginAttemptBucket.objects.values())))

    def test_headers_and_csrf_remain_enforced(self):
        response=self.client.get(reverse('login'))
        self.assertIn("object-src 'none'",response['Content-Security-Policy'])
        self.assertIn("frame-ancestors 'none'",response['Content-Security-Policy'])
        self.assertEqual(response['Referrer-Policy'],'same-origin')
        self.assertEqual(response['X-Content-Type-Options'],'nosniff')
        self.assertIn('no-store',response['Cache-Control'])
        csrf=Client(enforce_csrf_checks=True)
        self.assertEqual(csrf.post(reverse('login'),{'username':'ops','password':'x'}).status_code,403)

    def test_services_are_controlled_by_the_catalogue(self):
        data={'name':'Agent Test','registration':'TEST-99','service':SERVICES[0],'job':'Archiviste','grade':'Agent'}
        self.assertTrue(AgentForm(data).is_valid())
        self.assertFalse(AgentForm({**data,'service':'Service arbitraire injecté'}).is_valid())

    def test_dashboards_are_distinct_and_only_show_assigned_tasks(self):
        for role in ['OPS','SECAD','AP','DIRCAB']:
            user=get_user_model().objects.create_user('dashboard-'+role)
            user.groups.add(Group.objects.get_or_create(name='SIGDA_'+role)[0])
            self.client.force_login(user)
            response=self.client.get(reverse('overview'))
            self.assertContains(response,'Tableau de bord '+role)
            self.assertEqual(response.context['dashboard']['cards'][0][1],0)
        self.client.force_login(self.user)
        record=DocumentRequest.objects.create(owner=self.user,agent_key='saisie',document_key='attestation-service')
        secad=get_user_model().objects.get(username='dashboard-SECAD')
        ValidationTask.objects.create(request=record,stage='SECAD',assignee=secad,assigned_by=self.user,snapshot_hash='x')
        self.assertEqual(self.client.get(reverse('overview')).context['dashboard']['cards'][0][1],0)

    def test_overlong_password_is_rejected_before_password_hashing(self):
        with patch('django.contrib.auth.forms.authenticate') as authenticate:
            response=self.client.post(reverse('login'),{'username':self.user.username,'password':'x'*1025})
            self.assertEqual(response.status_code,200)
            authenticate.assert_not_called()
