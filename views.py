from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.core.context_processors import csrf
from forms import CustomRegistrationForm

from django_auth.models import UserProfile
import datetime, random, hashlib
from django.shortcuts import render_to_response, get_object_or_404
from django.core.mail import send_mail


def index(request):
    return HttpResponseRedirect('/django_auth/login')


# Login function
def login(request):
    c = {}
    c.update(csrf(request))
    return render_to_response('login_register.html', c)


# Authentications
def dj_auth(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user = auth.authenticate(username=username, password=password)

    if user is not None:
        auth.login(request, user)
        return HttpResponseRedirect('/django_auth/profile')
    else:
        return HttpResponseRedirect('/django_auth/invalid')


# Show user profile
def profile(request):
    return render_to_response('profile.html', {'full_name': request.user.username})


# No user
def invalid(request):
    return render_to_response('invalid.html')


# Logout
def logout(request):
    auth.logout(request)
    return render_to_response('logout.html')


# Register user
def register_user(request):
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            form.save()

            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            activation_key = hashlib.sha1(salt + email).hexdigest()
            key_expires = datetime.datetime.today() + datetime.timedelta(2)

            # Retrieve user
            user = User.objects.get(username=username)

            # Save profile
            new_profile = UserProfile(user=user, activation_key=activation_key,
                                      key_expires=key_expires)
            new_profile.save()

            # Send email with activation key
            email_subject = 'Account confirmation'
            email_body = "Hi %s, you have successfully registered but just one last step to get started. To activate your account, click this link within \
            48hours http://127.0.0.1:8000/accounts/confirm/%s" % (username, activation_key)

            send_mail(email_subject, email_body, 'mail@localhost',
                      [email], fail_silently=False)

            return HttpResponseRedirect('/django_auth/register_success')

    args = {}
    args.update(csrf(request))

    args['form'] = CustomRegistrationForm()

    return render_to_response('login_register.html', args)


# Register success
def register_success(request):
    return render_to_response('register_success.html')


# Confirm email
def confirm(request, activation_key):
    if request.user.is_authenticated():
        return render_to_response('confirm.html', {'has_account': True})
    user_profile = get_object_or_404(UserProfile,
                                     activation_key=activation_key)
    if user_profile.key_expires < datetime.datetime.today():
        return render_to_response('confirm.html', {'expired': True})
    user_account = user_profile.user
    user_account.is_active = True
    user_account.save()
    return render_to_response('confirm.html', {'success': True})
