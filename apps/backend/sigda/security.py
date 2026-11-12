from datetime import timedelta

from django.conf import settings
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import MaxLengthValidator
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.cache import patch_cache_control

from .models import LoginAttemptBucket


def attempt_keys(request):
    address=request.META.get('REMOTE_ADDR','')
    username=request.POST.get('username','').strip().casefold()[:150]
    return [salted_hmac('sigda-login',value,algorithm='sha256').hexdigest()
            for value in ('ip:'+address, 'pair:'+address+'\0'+username)]


def reserve_attempt(request):
    now=timezone.now();cutoff=now-timedelta(minutes=15)
    with transaction.atomic():
        for key,limit in zip(attempt_keys(request),(settings.SIGDA_LOGIN_IP_LIMIT,5)):
            LoginAttemptBucket.objects.get_or_create(key=key,defaults={'started_at':now})
            LoginAttemptBucket.objects.filter(key=key,started_at__lte=cutoff).update(started_at=now,attempts=0)
            if not LoginAttemptBucket.objects.filter(key=key,attempts__lt=limit).update(attempts=F('attempts')+1):
                return False
    return True


class BoundedAuthenticationForm(AuthenticationForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["password"].max_length=1024
        self.fields["password"].validators.append(MaxLengthValidator(1024))


class ProtectedLoginView(LoginView):
    form_class=BoundedAuthenticationForm
    authentication_form=BoundedAuthenticationForm
    def post(self,request,*args,**kwargs):
        if not reserve_attempt(request):
            form=self.form_class(request=request)
            response=self.render_to_response(self.get_context_data(form=form,login_throttled=True),status=429)
            response['Retry-After']='900'
            return response
        return super().post(request,*args,**kwargs)

    def form_valid(self,form):
        LoginAttemptBucket.objects.filter(key=attempt_keys(self.request)[1]).delete()
        return super().form_valid(form)


class ResponseSecurityMiddleware:
    def __init__(self,get_response):
        self.get_response=get_response

    def __call__(self,request):
        response=self.get_response(request)
        response['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        response['Referrer-Policy']='same-origin'
        response['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if not request.path.startswith('/static/') and request.path not in ['/manifest.webmanifest','/sw.js','/offline.html']:
            patch_cache_control(response,private=True,no_store=True,no_cache=True,must_revalidate=True)
        return response
