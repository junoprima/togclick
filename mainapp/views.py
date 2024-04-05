from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from pathlib import Path
import json
import ijson

#change limit for show more orders
def process_large_json(limit=1000):
    file_path = 'mainapp/order_history.json'
    
    with open(file_path, 'rb') as file: 
        data = ijson.items(file, 'item')
        data_subset = [obj for _, obj in zip(range(limit), data)]
    
    return data_subset


#def load_json_data():
#    file_path = Path(settings.BASE_DIR, 'mainapp/test_json.json')
    
#    with open(file_path, 'r') as file:
#        data = json.load(file)
    
#    return data

def read_sql_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

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
    data = process_large_json()
    return render(request, 'mainapp/dashboard.html', {'data': data})


def logged_out_view(request):
    return render(request, 'logged_out.html')
