from django.shortcuts import redirect, render
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def index(request):
    return render(request, "index.html")

def userLogin(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        # Django's authenticate checks the hashed password in the DB.
        # We pass the email as the username since that's how we registered them.
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("index") # Redirect to index after login
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, "userLogin.html")
    return render(request, "userLogin.html")

def userLogout(request):
    logout(request)
    return redirect("index")

def userRegistration(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        
        if password == confirm_password:
            # Check if user already exists via email (which acts as their username)
            if User.objects.filter(username=email).exists():
                messages.error(request, "Email is already registered.")
                return render(request, "userRegistration.html")
            
            # create_user automatically hashes the password!
            # We map their email to the 'username' field so Django auth works natively.
            username_part = email.split('@')[0]
            new_user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=username_part,
            )
            # Log the user in immediately after registering
            login(request, new_user)
            return redirect("index") # Redirect to index after registration
        else:
            messages.error(request, "Passwords do not match.")
            return render(request, "userRegistration.html")
            
    return render(request, "userRegistration.html")