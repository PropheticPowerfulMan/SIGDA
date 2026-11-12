from hashlib import sha256
from urllib.parse import urlencode
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse

from .composition_schema import compose_text
from .document_identity import identity, composed_identity
from .models import DocumentRequest, DocumentAccess
from .workflow import payload_digest, new_task
from .pdf import FOOTER


class IdentityTests(SimpleTestCase):
    def test_semantic_identity_is_deterministic_order_independent_and_versioned(self):
        args=('attestation-service','SPEC-ATS-UNIT-2026','12 novembre 2026','personnalise','Texte démo.')
        a=identity(*args,{'name':'Agent fictif','place':'Kinshasa'})
        self.assertEqual(a,identity(*args,{'place':'Kinshasa','name':'Agent fictif'}))
        self.assertNotEqual(a['hash'],identity(*args,{'name':'Agent fictif','place':'Goma'})['hash'])
        self.assertNotEqual(a['hash'],identity(*args,{'name':'Agent fictif','place':'Kinshasa'},revision=2)['hash'])
        self.assertNotEqual(a['hash'],identity(*args,{'name':'Agent fictif','place':'Kinshasa'},document_id=uuid4())['hash'])


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class IntegrityRegisterTests(TestCase):
    def setUp(self):
        self.users={}
        for role in ['OPS','SECAD','AP','DIRCAB']:
            user=get_user_model().objects.create_user('dna-'+role.lower());user.groups.add(Group.objects.get_or_create(name='SIGDA_'+role)[0]);self.users[role]=user
        self.other=get_user_model().objects.create_user('unrelated-ops');self.other.groups.add(Group.objects.get(name='SIGDA_OPS'))
        data={'kind':'attestation-service','wording':'classique','name':'Agent fictif ADN','registration':'DEMO-DNA-001','service':'Archives','job':'Archiviste','grade':'Agent','issuer_service':'Direction administrative','place':'Kinshasa','issue_date':'2026-11-12','signatory':'Autorité de démonstration','signatory_role':'Directeur','since':'2024-01-01','purpose':'compléter le dossier'}
        payload={'data':data,'reference':'SPEC-ATS-DNA-2026','text':compose_text(data)}
        self.record=DocumentRequest.objects.create(owner=self.users['OPS'],document_key=data['kind'],agent_key='saisie',payload=payload,payload_hash=payload_digest(payload))
        new_task(self.record,'OPS',self.users['OPS'],self.users['OPS'])
        self.url=reverse('verify_document',args=[self.record.pk]);self.dna=composed_identity(payload,str(self.record.pk),1)
        self.query={'revision':1,'dna':self.dna['hash']}

    def test_private_scoped_verification_rejects_forged_and_stale_identifiers(self):
        self.assertEqual(self.client.get(self.url,self.query).status_code,302)
        self.client.force_login(self.other);self.assertEqual(self.client.get(self.url,self.query).status_code,404)
        self.client.force_login(self.users['OPS']);response=self.client.get(self.url,self.query)
        self.assertEqual(response.status_code,200);self.assertFalse(response.context['approved']);self.assertContains(response,'encore dans le circuit')
        self.assertEqual(DocumentAccess.objects.filter(action='integrity_check').count(),1)
        self.assertEqual(self.client.get(self.url,{**self.query,'dna':'0'*64}).status_code,409)
        self.assertEqual(self.client.get(self.url,{**self.query,'revision':2}).status_code,409)
        self.assertEqual(self.client.get(self.url,{'revision':1}).status_code,400)
        self.record.payload['data']['place']='Goma';self.record.save(update_fields=['payload'])
        self.assertEqual(self.client.get(self.url,self.query).status_code,409)

    def test_approved_pdf_contains_social_uri_links_and_a_private_dna_qr(self):
        for role,target in [('OPS','SECAD'),('SECAD','AP'),('AP','DIRCAB'),('DIRCAB',None)]:
            self.record.refresh_from_db();self.client.force_login(self.users[role]);data={'action':'submit' if role=='OPS' else 'approve','revision':self.record.revision,'cycle':self.record.cycle}
            if target:data['assignee']=self.users[target].pk
            self.assertEqual(self.client.post(reverse('request_transition',args=[self.record.pk]),data).status_code,302)
        self.record.refresh_from_db();pdf=bytes(self.record.issued_pdf)
        self.assertEqual(sha256(pdf).hexdigest(),self.record.issued_hash)
        self.assertIn(self.dna['hash'].encode(),pdf)
        for item in FOOTER['social']:self.assertIn(item['url'].encode(),pdf)
        self.assertIn(self.url.encode(),pdf)
        result=self.client.get(self.url,self.query);self.assertEqual(result.status_code,200);self.assertTrue(result.context['approved'])
        self.record.issued_pdf=pdf+b'tampered';self.record.save(update_fields=['issued_pdf'])
        self.assertEqual(self.client.get(self.url,self.query).status_code,409)
        self.assertEqual(self.client.get(reverse('saved_document',args=[self.record.pk,'pdf'])).status_code,409)
