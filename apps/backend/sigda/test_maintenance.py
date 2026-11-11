from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import AgentRecord, MaintenanceEvent, ServiceValidity, SupportTicket
from .service_policy import annual_end, policy


class MaintenanceTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.ops = users.objects.create_user('ops-test')
        self.ops.groups.add(Group.objects.get_or_create(name='SIGDA_OPS')[0])
        self.support = users.objects.create_user('support-test', is_staff=True)
        self.support.groups.add(Group.objects.get_or_create(name='SIGDA_MAINTENANCE')[0])

    def upload(self, text):
        return self.client.post(reverse('maintenance'), {'action': 'agents', 'owner': self.ops.pk, 'reason': 'Demande de test',
            'csv_file': SimpleUploadedFile('agents.csv', text.encode('utf-8'), content_type='text/csv')})

    def test_annual_calendar_boundaries_and_reminder(self):
        self.assertEqual(policy(date(2026, 12, 31))['state'], 'preparation')
        self.assertEqual(policy(date(2027, 1, 1))['state'], 'active')
        self.assertEqual(policy(date(2027, 12, 2))['state'], 'reminder')
        self.assertEqual(policy(date(2027, 12, 31))['days'], 1)
        self.assertTrue(policy(date(2028, 1, 1))['expired'])
        self.assertEqual(annual_end(date(2028, 2, 29)), date(2029, 2, 28))

    def test_all_operational_roles_are_denied_technical_administration(self):
        for role in ['OPS', 'SECAD', 'AP', 'DIRCAB']:
            user = get_user_model().objects.create_user('role-' + role)
            user.groups.add(Group.objects.get_or_create(name='SIGDA_' + role)[0])
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('maintenance')).status_code, 403)
            self.assertEqual(self.client.post(reverse('maintenance'), {'action': 'validity', 'starts_on': '2028-01-01', 'reason': 'Test'}).status_code, 403)
            self.assertEqual(self.client.post(reverse('agent_save'), {}).status_code, 403)
        self.assertFalse(ServiceValidity.objects.exists())

    def test_maintenance_import_is_atomic_and_updates_by_matricule(self):
        self.client.force_login(self.support)
        header = 'name,registration,service,job,grade\n'
        valid = 'Agent Fictif,test-099,Archives,Archiviste,Agent\n'
        self.assertEqual(self.upload(header + valid).status_code, 302)
        agent = AgentRecord.objects.get(owner=self.ops)
        self.assertEqual(agent.registration, 'TEST-099')
        self.assertEqual(self.upload(header + valid.replace('Agent Fictif', 'Agent Corrigé')).status_code, 302)
        agent.refresh_from_db(); self.assertEqual(agent.name, 'Agent Corrigé')
        self.assertEqual(AgentRecord.objects.count(), 1)
        self.assertEqual(MaintenanceEvent.objects.filter(action='agents_import').count(), 2)
        before = AgentRecord.objects.count()
        self.upload(header + valid.replace('test-099', 'new-001') + 'Dossier incomplet\n')
        self.assertEqual(AgentRecord.objects.count(), before)

    def test_only_maintainer_can_renew_and_changes_are_journaled(self):
        self.client.force_login(self.support)
        response = self.client.post(reverse('maintenance'), {'action': 'validity', 'starts_on': '2028-01-01', 'reason': 'Renouvellement annuel validé'})
        self.assertEqual(response.status_code, 302)
        window = ServiceValidity.objects.get()
        self.assertEqual(window.expires_on, date(2029, 1, 1))
        self.assertEqual(window.updated_by, self.support)
        self.assertEqual(MaintenanceEvent.objects.get().details['previous_start'], '2027-01-01')

    def test_expiration_blocks_new_document_generation_and_support_remains_available(self):
        self.client.force_login(self.ops)
        with patch('sigda.service_policy.timezone.localdate', return_value=date(2028, 1, 1)):
            self.assertEqual(self.client.post(reverse('compose_preview'), {}).status_code, 403)
            self.assertEqual(self.client.post(reverse('compose_save'), {}).status_code, 403)
            self.assertEqual(self.client.get(reverse('support')).status_code, 200)
            response = self.client.post(reverse('support'), {'category': 'renewal', 'details': 'Merci de traiter le renouvellement annuel.'})
            self.assertEqual(response.status_code, 302)
        self.assertEqual(SupportTicket.objects.get().owner, self.ops)

    def test_tickets_are_scoped_and_maintenance_can_respond(self):
        ticket = SupportTicket.objects.create(owner=self.ops, category='agent_add', details='Ajout demandé : référence DEMO-TEST-777')
        other = get_user_model().objects.create_user('other-test')
        self.client.force_login(other)
        self.assertNotContains(self.client.get(reverse('support')), 'DEMO-TEST-777')
        self.client.force_login(self.support)
        self.assertContains(self.client.get(reverse('maintenance')), 'DEMO-TEST-777')
        response = self.client.post(reverse('maintenance'), {'action': 'ticket', 'ticket_id': ticket.pk, 'state': 'processing', 'response': 'Prise en charge par la maintenance.'})
        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db(); self.assertEqual(ticket.handled_by, self.support)
        self.assertEqual(ticket.state, 'processing')
