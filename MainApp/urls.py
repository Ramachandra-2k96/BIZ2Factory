from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import seller_dashboard

urlpatterns = [
     path('', views.home, name='home'),
     path('signup/', views.signup_view, name='signup'),
     path('accounts/login/', views.login_view, name='login'),
     path('accounts/logout/', views.LogoutView.as_view(), name='logout'),
    
     path('profile/', views.profile_view, name='profile'),
    
     path('search-companies/', seller_dashboard, name='company-search'),
    
     # Password Reset URLs
     path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
     path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
     path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
     path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'), 
    
     path('fill',views.fill,name='fill'),
     path('api/materials/', views.get_materials, name='get_materials'),
     
     path('add-inventory/', views.add_inventory, name='add_inventory'),
     path('inventory/', views.inventory_management, name='inventory_management'),
     path('inventory/edit/<int:inventory_id>/', views.edit_inventory, name='edit_inventory'),
     path('inventory/delete/<int:inventory_id>/', views.delete_inventory, name='delete_inventory'),
     
     path('contact-company/<int:company_id>/', views.contact_company, name='contact_company'),
     path('notify-top-companies/', views.notify_top_companies, name='notify_top_companies'),
]
