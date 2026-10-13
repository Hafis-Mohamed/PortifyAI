from django.shortcuts import redirect, render
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone

from Portfolio.models import Portfolio, PortfolioURL, PortfolioView
from Portfolio.services.analytics import get_tracking_base, is_public_base

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

        if context["portfolio_url"] and context["portfolio"]:
            portfolio = context["portfolio"]
            # Counts are stored on the Portfolio row by the tracking endpoint
            tracking_base = get_tracking_base(request)
            context["analytics"] = {
                "page_views": portfolio.view_count,
                "unique_visitors": portfolio.unique_visitor_count,
                "last_viewed_at": portfolio.last_viewed_at,
                "views_today": PortfolioView.objects.filter(
                    portfolio=portfolio,
                    created_at__gte=timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0),
                ).count(),
                "status": "Active (Real-Time)",
                "is_enabled": True,
                "tracking_reachable": is_public_base(tracking_base),
                "username": request.user.username,
                "recent_views": PortfolioView.objects.filter(portfolio=portfolio)[:5]
            }
        else:
            context["analytics"] = None
            
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