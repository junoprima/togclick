from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to the dashboard
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'mainapp/login.html')

@login_required
def dashboard_view(request):
    return render(request, 'mainapp/dashboard.html')


def logged_out_view(request):
    return render(request, 'logged_out.html')
