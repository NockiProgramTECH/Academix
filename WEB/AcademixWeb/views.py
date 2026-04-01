from os import read

from django.shortcuts import render

def home(request):
    return render(request, 'index.html')

def prof_login(request):
    """Simple view for professor login page"""
    return render(request, 'prof_login.html')

def parent_login(request):
    """Simple view for parent login page"""
    return render(request, 'parent_login.html')





def parent_register(request):
    """Simple view for parent registration page"""
    return render(request, 'parent_register.html')
