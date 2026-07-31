from django.shortcuts import render

def index(request):
    return render(request,"index.html")

def userRegistration(request):
    return render(request,"userRegistration.html")