from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from Portfolio.models import Portfolio, Resume
from Portfolio.services.vercel_deploy import delete_from_vercel

User = get_user_model()

# Utility to check if user is admin
def is_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin, login_url='/user_login/')
def dashboard(request):
    # Pass some basic stats for the dashboard
    total_users = User.objects.count()
    total_resumes = Resume.objects.count()
    total_portfolios = Portfolio.objects.count()
    
    recent_portfolios = Portfolio.objects.select_related('user').order_by('-updated_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_resumes': total_resumes,
        'total_portfolios': total_portfolios,
        'recent_portfolios': recent_portfolios,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@user_passes_test(is_admin, login_url='/user_login/')
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
    }
    return render(request, 'admin_panel/manage_users.html', context)

@user_passes_test(is_admin, login_url='/user_login/')
def manage_portfolios(request):
    portfolios = Portfolio.objects.select_related('user').order_by('-updated_at')
    context = {
        'portfolios': portfolios
    }
    return render(request, 'admin_panel/manage_portfolios.html', context)

@user_passes_test(is_admin, login_url='/user_login/')
def delete_portfolio(request, portfolio_id):
    if request.method == 'POST':
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        
        # Delete from Vercel if it exists
        project_name = f"portifyai-{portfolio.user.username}"
        delete_from_vercel(project_name)
        
        portfolio.delete()
        messages.success(request, "Portfolio deleted successfully from database and Vercel.")
    return redirect('admin_panel:manage_portfolios')

@user_passes_test(is_admin, login_url='/user_login/')
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if not user.is_superuser:
            user.delete()
            messages.success(request, "User deleted successfully.")
        else:
            messages.error(request, "Cannot delete superuser.")
    return redirect('admin_panel:manage_users')
