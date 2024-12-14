from django.shortcuts import render, redirect
from django.core.cache import cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RegisterForm, LoginForm
import bleach
from django.core.mail import send_mail
from django.conf import settings

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                username = bleach.clean(form.cleaned_data.get("username"))
                password = form.cleaned_data.get("password")
                email = form.cleaned_data.get("email")
                
                print(f"\nEmail Address: {email}\n")
                print(form.cleaned_data)
                
                newUser = User(username=username)
                newUser.email = email
                newUser.set_password(password)
                newUser.save()              
                
                send_mail(
                    'Account Created',
                    'Your account has been created. Welcome to the Software Science Blog community.',
                    settings.EMAIL_HOST_USER,
                    [newUser.email,],
                    fail_silently=False,
                )
                
                login(request, newUser)
                messages.success(request, "You have successfully registered...")
                return redirect("index")
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})

@sensitive_post_parameters()
@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def loginUser(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = bleach.clean(form.cleaned_data.get("username"))
            password = form.cleaned_data.get("password")

            user = authenticate(username=username, password=password)

            if user is None:
                messages.error(request, "Username or Password is incorrect")
            else:
                login(request, user)
                messages.success(request, "You have successfully logged in")
                return redirect("index")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})

@never_cache
@require_http_methods(["GET", "POST"])
def logoutUser(request):
    logout(request)
    
    # Clear user-specific caches
    cache.delete(f'user_dashboard_{request.user.id}')
    
    messages.success(request, "You have successfully logged out")
    return redirect("index")
