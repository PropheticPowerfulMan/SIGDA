import csv
from uuid import UUID
from io import StringIO

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .composition import AgentForm
from .models import AgentRecord, MaintenanceEvent, ServiceValidity, SupportTicket
from .roles import is_maintainer, role_for
from .service_policy import annual_end, policy
from .usage import log_usage


class TicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['category', 'details']
        labels = {'category': 'Nature de l’intervention', 'details': 'Objet et référence du dossier concerné'}
        widgets = {'details': forms.Textarea(attrs={'rows': 4})}


class ValidityForm(forms.Form):
    starts_on = forms.DateField(label='Début de la nouvelle période annuelle', widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    reason = forms.CharField(label='Motif de configuration ou de renouvellement', min_length=3, max_length=300)


class ImportForm(forms.Form):
    owner = forms.ModelChoiceField(label='Compte OPS qui utilisera ces dossiers', queryset=get_user_model().objects.none())
    csv_file = forms.FileField(label='Fichier CSV des agents (UTF-8, 1 Mo maximum)')
    reason = forms.CharField(label='Référence de la demande ou motif', min_length=3, max_length=300)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = get_user_model().objects.filter(is_active=True, groups__name='SIGDA_OPS').distinct()
        self.fields['owner'].queryset = get_user_model().objects.filter(pk__in=[u.pk for u in users if role_for(u) == 'OPS'])

    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if file.size > 1024 * 1024:
            raise forms.ValidationError('Le fichier dépasse 1 Mo.')
        try:
            text = file.read().decode('utf-8-sig')
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=',;\t')
            rows = csv.DictReader(StringIO(text), dialect=dialect)
            fields = {'name', 'registration', 'service', 'job', 'grade'}
            if set(rows.fieldnames or []) != fields:
                raise ValueError('Colonnes requises : name, registration, service, job, grade.')
            result = []
            registrations = set()
            for line, values in enumerate(rows, 2):
                if len(result) >= 1000 or None in values or any(value is None for value in values.values()):
                    raise ValueError(f'Ligne {line} invalide ou limite de 1 000 agents dépassée.')
                form = AgentForm(values)
                if not form.is_valid():
                    raise ValueError(f'Ligne {line} : vérifiez les cinq champs administratifs.')
                data = form.cleaned_data
                if data['registration'] in registrations:
                    raise ValueError(f'Matricule présent plusieurs fois, ligne {line}.')
                registrations.add(data['registration']); result.append(data)
            if not result:
                raise ValueError('Le fichier ne contient aucun agent.')
            return result
        except (UnicodeError, csv.Error, ValueError) as error:
            raise forms.ValidationError(str(error)) from error


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def support(request):
    category = request.GET.get('category', 'assistance')
    if category not in dict(SupportTicket.CATEGORIES):
        category = 'assistance'
    form = TicketForm(request.POST or None, initial={'category': category})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            ticket = form.save(commit=False); ticket.owner = request.user; ticket.save()
            log_usage(request.user, 'support_request')
        request.session['sigda-feedback'] = 'Votre demande est enregistrée dans la file de maintenance.'
        return redirect('support')
    return render(request, 'support.html', {'current_view': 'support', 'current_label': 'Maintenance et assistance',
        'ticket_form': form, 'tickets': SupportTicket.objects.filter(owner=request.user)[:30]})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def administration(request):
    if not is_maintainer(request.user):
        raise PermissionDenied('Cet espace est réservé à l’équipe de maintenance habilitée.')
    validity_form = ValidityForm(initial={'starts_on': policy()['start']})
    import_form = ImportForm()
    problem = ''
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'validity':
            validity_form = ValidityForm(request.POST)
            if validity_form.is_valid():
                start = validity_form.cleaned_data['starts_on']; end = annual_end(start); previous = policy()
                with transaction.atomic():
                    ServiceValidity.objects.update_or_create(pk=1, defaults={'starts_on': start, 'expires_on': end, 'updated_by': request.user})
                    MaintenanceEvent.objects.create(actor=request.user, action='validity_update', details={
                        'previous_start': previous['start'].isoformat(), 'previous_end': previous['end'].isoformat(),
                        'start': start.isoformat(), 'end': end.isoformat(), 'reason': validity_form.cleaned_data['reason']})
                request.session['sigda-feedback'] = 'L’opération de maintenance a été enregistrée et journalisée.'
                return redirect('maintenance')
        elif action == 'agents':
            import_form = ImportForm(request.POST, request.FILES)
            if import_form.is_valid():
                owner = import_form.cleaned_data['owner']; created = 0; updated = 0
                with transaction.atomic():
                    for values in import_form.cleaned_data['csv_file']:
                        registration = values['registration']
                        _, added = AgentRecord.objects.update_or_create(owner=owner, registration=registration,
                            defaults={key: value for key, value in values.items() if key != 'registration'})
                        created += int(added); updated += int(not added)
                    MaintenanceEvent.objects.create(actor=request.user, action='agents_import', details={
                        'owner': owner.get_username(), 'created': created, 'updated': updated, 'reason': import_form.cleaned_data['reason']})
                    log_usage(request.user, 'agents_import')
                request.session['sigda-feedback'] = 'L’opération de maintenance a été enregistrée et journalisée.'
                return redirect('maintenance')
        elif action == 'ticket':
            try:
                ticket_id = UUID(request.POST.get('ticket_id', ''))
            except (ValueError, TypeError):
                raise Http404
            ticket = get_object_or_404(SupportTicket, pk=ticket_id)
            state = request.POST.get('state'); response = request.POST.get('response', '').strip()
            if state not in dict(SupportTicket.STATES) or not response or len(response) > 1000:
                problem = 'Indiquez un état valide et une réponse de 1 à 1 000 caractères.'
            else:
                with transaction.atomic():
                    ticket.state = state; ticket.response = response; ticket.handled_by = request.user; ticket.save()
                    MaintenanceEvent.objects.create(actor=request.user, action='ticket_update', details={'ticket': str(ticket.pk), 'state': state})
                request.session['sigda-feedback'] = 'L’opération de maintenance a été enregistrée et journalisée.'
                return redirect('maintenance')
        else:
            problem = 'Action de maintenance inconnue.'
    labels = {'agents_import': 'Import des agents', 'validity_update': 'Période annuelle actualisée', 'ticket_update': 'Suivi d’une intervention'}
    journal = []
    for event in MaintenanceEvent.objects.select_related('actor')[:30]:
        details = event.details
        summary = details.get('reason', '')
        if event.action == 'agents_import':
            summary = f"{details.get('created', 0)} ajout(s), {details.get('updated', 0)} actualisation(s) pour le compte {details.get('owner', '')}. {summary}"
        elif event.action == 'validity_update':
            summary = f"Début : {details.get('start', '')} ; échéance exclusive : {details.get('end', '')}. {summary}"
        elif event.action == 'ticket_update':
            summary = f"Demande {details.get('ticket', '')} : {dict(SupportTicket.STATES).get(details.get('state'), '')}."
        journal.append((event, labels.get(event.action, 'Intervention technique'), summary))
    return render(request, 'maintenance.html', {'current_view': 'maintenance', 'current_label': 'Administration technique',
        'validity_form': validity_form, 'import_form': import_form, 'problem': problem,
        'all_tickets': SupportTicket.objects.select_related('owner')[:50],
        'maintenance_events': journal})
