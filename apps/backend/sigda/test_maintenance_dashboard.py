from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.staticfiles import finders
from django.contrib.sessions.models import Session
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import SupportTicket, MaintenanceEvent, UsageEvent, DocumentRequest


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class MaintenanceDashboardTests(TestCase):
    def setUp(self):
        self.ops=get_user_model().objects.create_user('cabinet-ops',password='Fictif-Test-2026!')
        self.ops.groups.add(Group.objects.get_or_create(name='SIGDA_OPS')[0])
        self.team=get_user_model().objects.create_user('equipe-technique',is_staff=True)
        self.team.groups.add(Group.objects.get_or_create(name='SIGDA_MAINTENANCE')[0])

    def test_technical_dashboard_receives_cabinet_requests_and_scopes_access(self):
        self.client.force_login(self.ops)
        self.assertEqual(self.client.get(reverse('maintenance_status')).status_code,403)
        self.assertEqual(self.client.get(reverse('activity')).status_code,403)
        self.client.post(reverse('support'),{'category':'app_update','details':'Demande de mise à jour fictive MAINT-777'})
        self.client.force_login(self.team)
        self.assertRedirects(self.client.get(reverse('overview')),reverse('maintenance'))
        self.assertContains(self.client.get(reverse('maintenance')),'MAINT-777')
        response=self.client.get(reverse('maintenance_status'));self.assertEqual(response.status_code,200);self.assertEqual(response.json()['counts']['open'],1)
        self.assertIn('no-store',response.headers['Cache-Control'])
        self.assertEqual(self.client.get(reverse('activity')).status_code,200)
        self.assertEqual(self.client.get(reverse('compose')).status_code,403)
        hidden=DocumentRequest.objects.create(owner=self.ops,document_key='attestation-service',agent_key='alpha',payload={'data':{'name':'Agent privé non divulgué'}})
        self.assertEqual(self.client.get(reverse('request_detail',args=[hidden.pk])).status_code,404)

    def test_followup_is_returned_to_requester_and_stale_forms_do_not_overwrite(self):
        ticket=SupportTicket.objects.create(owner=self.ops,category='assistance',details='Traitement fictif')
        stamp=ticket.updated_at.isoformat();self.client.force_login(self.team)
        data={'action':'ticket','ticket_id':ticket.pk,'expected_update':stamp,'state':'processing','response':'Prise en charge par notre équipe.'}
        self.assertEqual(self.client.post(reverse('maintenance'),data).status_code,302)
        self.assertEqual(self.client.post(reverse('maintenance'),{**data,'state':'resolved','response':'Ancien écran obsolète.'}).status_code,409)
        ticket.refresh_from_db();self.assertEqual(ticket.state,'processing');self.assertEqual(ticket.handled_by,self.team)
        self.assertEqual(MaintenanceEvent.objects.filter(action='ticket_update').count(),1)
        self.assertEqual(self.client.get(reverse('maintenance_status')).json()['counts']['processing'],1)
        self.client.force_login(self.ops);self.assertContains(self.client.get(reverse('support')),'Prise en charge par notre équipe.')

    def test_only_successful_login_popup_is_removed_and_guide_stays_demo_only(self):
        response=self.client.post(reverse('login'),{'username':self.ops.username,'password':'Fictif-Test-2026!'})
        self.assertEqual(response.status_code,302);self.assertNotIn('sigda-feedback',self.client.session)
        self.assertTrue(UsageEvent.objects.filter(actor=self.ops,action='login').exists())
        self.client.post(reverse('support'),{'category':'assistance','details':'Une autre action doit conserver sa confirmation.'})
        self.assertIn('sigda-feedback',self.client.session)
        self.client.logout();self.assertNotContains(self.client.get(reverse('login')),'data-demo-guide')
        self.assertIsNone(finders.find('guide-utilisateur-sigda-demo.pdf'))

    def test_maintenance_queue_is_paginated_and_filterable(self):
        SupportTicket.objects.bulk_create([SupportTicket(owner=self.ops,category='assistance',details='Demande '+str(i),state='processing' if i==0 else 'open') for i in range(20)])
        self.client.force_login(self.team)
        response=self.client.get(reverse('maintenance'));self.assertEqual(response.context['ticket_page'].paginator.count,20)
        self.assertEqual(len(response.context['all_tickets']),15)
        filtered=self.client.get(reverse('maintenance'),{'state':'processing'});self.assertEqual(filtered.context['ticket_page'].paginator.count,1)

    def test_background_polling_does_not_extend_an_unattended_session(self):
        self.client.force_login(self.team)
        key=self.client.session.session_key
        expires=timezone.now()+timedelta(minutes=10)
        Session.objects.filter(session_key=key).update(expire_date=expires)
        response=self.client.get(reverse('maintenance_status'))
        self.assertEqual(response.status_code,200)
        self.assertNotIn(settings.SESSION_COOKIE_NAME,response.cookies)
        self.assertEqual(Session.objects.get(session_key=key).expire_date,expires)
        self.client.get(reverse('maintenance'))
        self.assertGreater(Session.objects.get(session_key=key).expire_date,expires)
