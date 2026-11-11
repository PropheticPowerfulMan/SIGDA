from hashlib import sha256

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .composition import render_composed
from .composition_schema import compose_text
from .models import DocumentRequest, RequestEvent, ValidationTask, UsageEvent
from .workflow import payload_digest, new_task


class WorkflowTests(TestCase):
    def setUp(self):
        self.accounts = {}
        for role in ('OPS', 'SECAD', 'AP', 'DIRCAB'):
            user = get_user_model().objects.create_user(role.lower())
            user.groups.add(Group.objects.get_or_create(name='SIGDA_' + role)[0])
            self.accounts[role] = user
        self.other = get_user_model().objects.create_user('other')
        self.other.groups.add(Group.objects.get(name='SIGDA_SECAD'))
        data = {'kind': 'attestation-service', 'wording': 'classique', 'name': 'Agent Fictif', 'registration': 'DEMO-101',
                'service': 'Archives', 'job': 'Archiviste', 'grade': 'Agent', 'issuer_service': 'Direction administrative',
                'place': 'Kinshasa', 'issue_date': '2026-11-11', 'signatory': 'Responsable Démo', 'signatory_role': 'Directeur',
                'since': '2024-01-01', 'purpose': 'compléter le dossier'}
        payload = {'data': data, 'text': compose_text(data), 'reference': 'SPEC-ATS-DEMO-101-2026'}
        self.record = DocumentRequest.objects.create(owner=self.accounts['OPS'], agent_key='saisie', document_key=data['kind'], payload=payload, payload_hash=payload_digest(payload))
        new_task(self.record, 'OPS', self.accounts['OPS'], self.accounts['OPS'])

    def act(self, role, action, target=None, **extra):
        self.record.refresh_from_db()
        self.client.force_login(self.accounts[role])
        return self.client.post(reverse('request_transition', args=[self.record.pk]), {
            'action': action, 'revision': self.record.revision, 'cycle': self.record.cycle,
            **({'assignee': self.accounts[target].pk} if target else {}), **extra})

    def complete(self):
        for role, action, target in [('OPS', 'submit', 'SECAD'), ('SECAD', 'approve', 'AP'), ('AP', 'approve', 'DIRCAB'), ('DIRCAB', 'approve', None)]:
            self.assertEqual(self.act(role, action, target).status_code, 302)
        self.record.refresh_from_db()

    def test_named_four_stage_circuit_archives_one_immutable_printable_version(self):
        self.client.force_login(self.accounts['OPS'])
        url = reverse('saved_document', args=[self.record.pk, 'pdf'])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.act('OPS', 'submit', 'SECAD').status_code, 302)
        self.assertEqual(self.act('AP', 'approve', 'DIRCAB').status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('request_detail', args=[self.record.pk])).status_code, 404)
        self.assertEqual(self.act('SECAD', 'approve', 'AP').status_code, 302)
        self.assertEqual(self.act('AP', 'approve', 'DIRCAB').status_code, 302)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.act('DIRCAB', 'approve').status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'approved')
        self.assertEqual(self.record.issued_hash, sha256(bytes(self.record.issued_pdf)).hexdigest())
        archived = bytes(self.record.issued_pdf)
        self.assertTrue(archived.startswith(b'%PDF-'))
        self.assertIn(b'TimesNewRomanPSMT', archived)
        self.assertEqual(self.client.get(url).content, archived)
        self.assertEqual(self.record.accesses.count(), 1)
        self.assertEqual(self.record.tasks.filter(state='pending').count(), 0)
        self.assertEqual(self.act('DIRCAB', 'approve').status_code, 403)
        self.assertEqual(self.client.get(url).content, archived)

    def test_return_requires_reason_and_revalidation_of_new_revision(self):
        self.assertEqual(self.act('OPS', 'submit', 'SECAD').status_code, 302)
        self.assertEqual(self.act('SECAD', 'return').status_code, 400)
        self.assertEqual(self.act('SECAD', 'return', note='Corriger la date').status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'draft')
        task = self.record.tasks.get(state='pending')
        self.assertEqual(task.assignee, self.accounts['OPS'])
        self.assertEqual(self.act('OPS', 'submit', 'SECAD', revision=99).status_code, 409)
        self.assertEqual(self.act('OPS', 'submit', 'SECAD').status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.cycle, 2)
        self.assertEqual(self.act('SECAD', 'approve', 'AP').status_code, 302)
        self.assertEqual(self.act('AP', 'approve', 'DIRCAB').status_code, 302)
        # A substituted snapshot cannot inherit the approvals.
        self.record.refresh_from_db()
        self.record.payload['text'] += ' Altération.'
        self.record.save(update_fields=['payload'])
        self.assertEqual(self.act('DIRCAB', 'approve').status_code, 409)
        self.record.refresh_from_db()
        self.assertFalse(self.record.issued_pdf)

    def test_reject_is_final_and_only_dircab_may_use_it(self):
        self.assertEqual(self.act('OPS', 'submit', 'SECAD').status_code, 302)
        self.assertEqual(self.act('SECAD', 'reject', note='Refus').status_code, 404)
        self.assertEqual(self.act('SECAD', 'approve', 'AP').status_code, 302)
        self.assertEqual(self.act('AP', 'approve', 'DIRCAB').status_code, 302)
        self.assertEqual(self.act('DIRCAB', 'reject', note='Motif de refus final').status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'rejected')
        self.assertFalse(self.record.issued_pdf)

    def test_statistics_are_reserved_to_dircab_and_exclude_document_bodies(self):
        self.complete()
        for role in ('OPS', 'SECAD', 'AP'):
            self.client.force_login(self.accounts[role])
            self.assertEqual(self.client.get(reverse('activity')).status_code, 403)
            self.assertNotContains(self.client.get(reverse('overview')), 'title="Activité"')
        self.client.force_login(self.accounts['DIRCAB'])
        response = self.client.get(reverse('activity'))
        self.assertEqual(response.status_code, 200)
        data = response.context['statistics_data']
        self.assertEqual(len(data['records']), 1)
        self.assertEqual(len(data['records'][0]['tasks']), 4)
        self.assertNotIn('Agent Fictif', str(data))
        self.assertTrue(any(e['action'] == 'approve' for e in data['usage']))
        self.assertIn('no-store', response['Cache-Control'])

    def test_roles_cannot_prepare_or_modify_agent_data_and_ambiguous_roles_fail_closed(self):
        for role in ('SECAD', 'AP', 'DIRCAB'):
            self.client.force_login(self.accounts[role])
            self.assertEqual(self.client.get(reverse('compose')).status_code, 403)
            self.assertEqual(self.client.post(reverse('agent_save'), {}).status_code, 403)
        self.accounts['OPS'].groups.add(Group.objects.get(name='SIGDA_DIRCAB'))
        self.assertEqual(self.act('OPS', 'submit', 'SECAD').status_code, 403)
        self.assertEqual(self.client.get(reverse('activity')).status_code, 403)

    def test_final_archive_hash_is_verified_on_every_open(self):
        self.complete()
        self.record.issued_pdf = b'altered'
        self.record.save(update_fields=['issued_pdf'])
        self.assertEqual(self.client.get(reverse('saved_document', args=[self.record.pk, 'pdf'])).status_code, 409)
