from django.shortcuts import render, redirect
from django.http import HttpResponse


#user registration/login imports
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

def home(request):
    return render(request,
                  'home/home.html',
                 )

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'home/signup.html', {'form':form})

def about(request):
    return render(request, 'home/about.html')
