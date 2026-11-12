from django.utils import timezone
from .models import DocumentRequest, ValidationTask
from .roles import role_for

PROFILES = {
    'OPS': ('Préparation des documents', 'Préparez les dossiers, corrigez les retours et confiez le contrôle à SECAD.', 'Brouillons à préparer', 'draft'),
    'SECAD': ('Contrôle administratif', 'Contrôlez les données et les pièces des tâches qui vous sont attribuées.', 'Documents à contrôler', 'submitted'),
    'AP': ('Visa hiérarchique', 'Examinez les contrôles SECAD et donnez votre visa avant transmission à DIRCAB.', 'Visas à donner', 'ap'),
    'DIRCAB': ('Décision et supervision', 'Prenez les décisions finales et suivez les indicateurs institutionnels.', 'Décisions finales attendues', 'dircab'),
}


def dashboard_data(user):
    role=role_for(user)
    if role not in PROFILES:
        return None
    title, description, label, stage=PROFILES[role]
    tasks=ValidationTask.objects.filter(assignee=user)
    pending=tasks.filter(state='pending')
    cards=[(label,pending.count()),('Échéances dépassées',pending.filter(due_at__lt=timezone.now()).count()),
           ('Tâches terminées',tasks.exclude(state='pending').count()),('Retours effectués',tasks.filter(state='returned').count())]
    if role=='OPS':
        cards[2]=('Mes documents en validation',DocumentRequest.objects.filter(owner=user,status__in=['submitted','ap','dircab']).count())
        cards[3]=('Mes documents validés',DocumentRequest.objects.filter(owner=user,status='approved').count())
    return {'title':f'Tableau de bord {role}', 'subtitle':title,'description':description,'cards':cards,
            'tasks':pending.select_related('request').order_by('due_at','created_at')[:8]}
