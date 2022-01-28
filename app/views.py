import os
from datetime import datetime
from sqlite3 import Timestamp
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.core.files import File
from numpy import diag

from app.forms import AccountUpdateEmailForm, AccountUpdateNameForm, AccountUpdatePhoneForm, AccountUpdateUsernameForm, RegistrationForm, AccountAuthenticationForm
from app.models import Account, CoughingResult

from .knn.core import main

def welcome_view(request):
    context = {}
    return render(request, 'welcome.html', context)

def auth_view(request, *args, **kwargs):
    user = request.user
    if user.is_authenticated: 
        return redirect("dashboard")
    destination = get_redirect_if_exists(request)
    print("destination: " + str(destination))
    
    context = {}
    
    # login
    if 'login-btn' in request.POST:
        if request.POST:
            form = AccountAuthenticationForm(request.POST)
            if form.is_valid():
                email = request.POST['email']
                password = request.POST['password']
                user = authenticate(email=email, password=password)
                if user:
                    login(request, user)
                    if destination:
                        return redirect(destination)
                    return redirect("dashboard")

        else:
            form = AccountAuthenticationForm()

        context['login_form'] = form
    
    # register
    elif 'register-btn' in request.POST:
        if request.POST:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                form.save()
                # email = form.cleaned_data.get('email').lower()
                # raw_password = form.cleaned_data.get('password1')
                # account = authenticate(email=email, password=raw_password)
                # login(request, account)
                destination = kwargs.get("next")
                if destination:
                    return redirect(destination)
                return redirect('welcome')
            else:
                context['registration_form'] = form

        else:
            form = RegistrationForm()
            context['registration_form'] = form
        
    return render(request, "auth.html", context)

def get_redirect_if_exists(request):
	redirect = None
	if request.GET:
		if request.GET.get("next"):
			redirect = str(request.GET.get("next"))
	return redirect

def dashboard_view(request):
    context = {}
    return render(request, 'accounts/dashboard.html', context)

@csrf_exempt
def test(request):
    context = {}
    return render(request, 'accounts/test.html', context)    

# global variable for diagnose_code
diagnose_code = 0

@csrf_exempt
def diagnose_view(request):
    # request should be ajax and method should be POST.
    # if request.method == 'POST' and request.is_ajax(): 
    # is_ajax is deprecated and removed since django 4.0
    if request.method == 'POST': 
        
        # delete old audio
        request.user.coughing_audio.delete()
        
        # recieve audio blob from ajax
        file = request.FILES.get('audio')
        print(f'ajax file recieved: {file}')
                
        # save audio to user model
        request.user.coughing_audio.save("coughing_audio.wav", file)
        request.user.save()
        
        # ready for KNN identifier
        # 1=healthy, 2=symtomatic
        audio_path = os.path.join(settings.BASE_DIR, f'media_cdn\coughing_audio\{request.user.pk}')
        diagnose_code = main("coughing_audio.wav", audio_path)
        # request.user.diagnose_code = 2
        request.user.diagnose_code = diagnose_code
        request.user.save()
        
        # save coughing result to history
        testDateTime = datetime.now().strftime('%d/%m/%y %H:%M:%S')
        diagnose_string = ''
        if diagnose_code == 2:
            diagnose_string = 'POSITIVE'
        elif diagnose_code == 1:
            diagnose_string = 'NEGATIVE'
        else:
            diagnose_string = 'N/A'
        CoughingResult.objects.create(test_date_time=testDateTime, diagnose_status=diagnose_string, user=request.user)
        
        context = {}    
        return render(request, 'accounts/diagnose.html', context)
    
    context = {}    
    return render(request, 'accounts/diagnose.html', context)

def diagnose_result_view(request):
    context = {}
    return render(request, 'accounts/diagnose-result.html', context)

def profile_view(request):
    context = {}
    return render(request, 'accounts/profile.html', context)

def change_password_view(request):
    context = {}
    return render(request, 'accounts/updateProfile/changePassword.html', context)

def change_email_view(request):
    context = {}
    
    if 'update-btn' in request.POST:
        form = AccountUpdateEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = AccountUpdateEmailForm(initial = {"email": request.user.email,})
    
    context['update_form'] = form
    return render(request, 'accounts/updateProfile/changeEmail.html', context)

def change_username_view(request):
    context = {}
    
    if 'update-btn' in request.POST:
        form = AccountUpdateUsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = AccountUpdateUsernameForm(initial = {"username": request.user.username,})
    
    context['update_form'] = form
    return render(request, 'accounts/updateProfile/changeUsername.html', context)

def change_name_view(request):
    context = {}
    
    if 'update-btn' in request.POST:
        form = AccountUpdateNameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = AccountUpdateNameForm(initial = {"name": request.user.name,})
    
    context['update_form'] = form
    return render(request, 'accounts/updateProfile/changeName.html', context)

def change_phone_view(request):
    context = {}
    
    if 'update-btn' in request.POST:
        form = AccountUpdatePhoneForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = AccountUpdatePhoneForm(initial = {"phone": request.user.phone,})
    
    context['update_form'] = form
    return render(request, 'accounts/updateProfile/changePhone.html', context)

def clinic_nearby_view(request):
    context = {}
    return render(request, 'accounts/clinicNearby.html', context)

def history_view(request):
    context = {}
    
    # get the result list from logged in user
    coughing_result_list = CoughingResult.objects.filter(user=request.user)
    context['coughing_result_list'] = coughing_result_list
    
    return render(request, 'accounts/history.html', context)

def logout_view(request):
    logout(request)
    return redirect("welcome")