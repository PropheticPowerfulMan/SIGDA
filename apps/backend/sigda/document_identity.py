"""Versioned, deterministic identity of a document, independent of PDF bytes."""
from hashlib import sha256
import json
from uuid import UUID, uuid5, NAMESPACE_URL

SCHEMA = 'sigda-dna-v1'


def identity(key, reference, date_label, style, text, fields=None, document_id=None, revision=1):
    identifier=str(UUID(str(document_id))) if document_id else str(uuid5(NAMESPACE_URL,'sigda:'+key+':'+reference))
    envelope={'schema':SCHEMA,'id':identifier,'revision':int(revision),'model':key,'reference':reference,
              'date':date_label,'style':style,'body':text,'fields':fields or {}}
    digest=sha256(json.dumps(envelope,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
    return {'schema':SCHEMA,'id':identifier,'revision':int(revision),'hash':digest,
            'label':f'SGD-{UUID(identifier).hex[:12].upper()}-R{int(revision)}-{digest[:16].upper()}'}


def composed_identity(snapshot, document_id=None, revision=None):
    from .catalog import format_date
    from datetime import date
    data=snapshot['data']
    return identity(data['kind'],snapshot['reference'],format_date(date.fromisoformat(data['issue_date'])),
                    'personnalise',snapshot['text'],data,document_id or snapshot.get('id'),
                    revision if revision is not None else snapshot.get('base_revision',0)+1)
