from hashlib import sha256
from secrets import compare_digest
from urllib.parse import urlencode
import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_safe

from .document_identity import composed_identity
from .models import DocumentAccess, DocumentRequest


def base_link(request, identifier):
    return request.build_absolute_uri(reverse('verify_document',args=[identifier]))


def link_for(request, record, dna=None):
    dna=dna or composed_identity(record.payload,str(record.pk),record.revision)
    return base_link(request,record.pk)+'?'+urlencode({'revision':dna['revision'],'dna':dna['hash']})


@login_required
@require_safe
def verify(request, pk):
    from .workflow import visible_requests, payload_digest
    from .usage import log_usage
    record=get_object_or_404(visible_requests(request.user).exclude(payload={}),pk=pk)
    dna=composed_identity(record.payload,str(record.pk),record.revision)
    claimed=request.GET.get('dna','');revision=request.GET.get('revision','')
    well_formed=bool(re.fullmatch(r'[a-f0-9]{64}',claimed) and re.fullmatch(r'[1-9][0-9]{0,8}',revision)) and len(request.GET.getlist('dna'))==1 and len(request.GET.getlist('revision'))==1
    matches=well_formed and int(revision)==record.revision and compare_digest(claimed,dna['hash'])
    snapshot_ok=compare_digest(payload_digest(record.payload),record.payload_hash)
    archive_ok=not record.issued_pdf or compare_digest(sha256(bytes(record.issued_pdf)).hexdigest(),record.issued_hash)
    approved=record.status==DocumentRequest.Status.APPROVED and bool(record.issued_pdf)
    valid=bool(matches and snapshot_ok and archive_ok)
    DocumentAccess.objects.create(request=record,actor=request.user,action='integrity_check',file_hash=record.issued_hash or dna['hash'])
    log_usage(request.user,'verify_integrity',record)
    return render(request,'workflow/integrity.html',{'current_label':'Vérification du document','record':record,'dna':dna,
        'valid':valid,'approved':approved,'matches':matches,'snapshot_ok':snapshot_ok,'archive_ok':archive_ok,
        'detail_url':reverse('request_detail',args=[record.pk])+'#document-history'},status=200 if valid else 409 if well_formed else 400)
