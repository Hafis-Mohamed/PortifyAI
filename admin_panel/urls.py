from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.manage_users, name='manage_users'),
    path('portfolios/', views.manage_portfolios, name='manage_portfolios'),
    path('portfolios/<int:portfolio_id>/delete/', views.delete_portfolio, name='delete_portfolio'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]
