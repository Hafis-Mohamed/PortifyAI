from django.shortcuts import redirect, render
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from Portfolio.models import Portfolio, PortfolioURL

def index(request):
    show_dashboard = request.GET.get("show_dashboard") == "true"
    context = {"show_dashboard": show_dashboard}
    if request.user.is_authenticated:
        try:
            context["portfolio"] = Portfolio.objects.get(user=request.user)
        except Portfolio.DoesNotExist:
            context["portfolio"] = None
        
        try:
            context["portfolio_url"] = PortfolioURL.objects.get(user=request.user)
        except PortfolioURL.DoesNotExist:
            context["portfolio_url"] = None
            
    return render(request, "index.html", context)

def userLogin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        # Django's authenticate checks the hashed password in the DB.
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect admins to the custom admin panel
            if user.is_staff or user.is_superuser:
                return redirect("admin_panel:dashboard")
            return redirect("index") # Redirect to index after login
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "userLogin.html")
    return render(request, "userLogin.html")

def userLogout(request):
    logout(request)
    return redirect("index")

def userRegistration(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        
        # Make sure username is valid (no spaces, alphanumeric is best)
        if not username.isalnum():
            messages.error(request, "Username can only contain letters and numbers.")
            return render(request, "userRegistration.html")
            
        if password == confirm_password:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username is already taken.")
                return render(request, "userRegistration.html")
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email is already registered.")
                return render(request, "userRegistration.html")
            
            # create_user automatically hashes the password!
            new_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=username,
            )
            # Log the user in immediately after registering
            login(request, new_user)
            return redirect("index") # Redirect to index after registration
        else:
            messages.error(request, "Passwords do not match.")
            return render(request, "userRegistration.html")
            
    return render(request, "userRegistration.html")