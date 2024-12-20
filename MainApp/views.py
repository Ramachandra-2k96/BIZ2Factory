from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm , AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View
from .forms import SellerRegistrationForm, CompanyRegistrationForm, SellerUpdateForm, CompanyUpdateForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import TemplateView
from .models import Seller, Company

from django.shortcuts import render, get_object_or_404
from .models import Seller

def home(request):
    return render(request, 'MainApp/index.html')

def signup_view(request):
    seller_form = SellerRegistrationForm()
    company_form = CompanyRegistrationForm()

    if request.method == 'POST':
        role = request.POST.get('role')
        
        if role == 'seller':
            form = SellerRegistrationForm(request.POST, request.FILES)
            seller_form = form
            if form.is_valid():
                try:
                    user = form.save()  # This will create Seller instance
                    login(request, user)
                    messages.success(request, 'Seller account created successfully!')
                    return redirect('home')
                except Exception as e:
                    messages.error(request, f'Error creating seller account: {str(e)}')
        
        elif role == 'company':
            form = CompanyRegistrationForm(request.POST, request.FILES)
            company_form = form
            if form.is_valid():
                try:
                    user = form.save()  # This will create Company instance
                    login(request, user)
                    messages.success(request, 'Company account created successfully!')
                    return redirect('home')
                except Exception as e:
                    messages.error(request, f'Error creating company account: {str(e)}')
        
        else:
            messages.error(request, 'Please select a role (Seller or Company)')
            
        if 'form' in locals() and not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")

    return render(request, 'MainApp/signup.html', {
        'seller_form': seller_form,
        'company_form': company_form
    })

@login_required
def profile_view(request):
    """
    Display and update user profile.
    """
    from .models import Seller, Company
    
    if request.method == 'POST':
        if Seller.is_user_seller(request.user):
            form = SellerUpdateForm(
                request.POST, 
                request.FILES, 
                instance=request.user.seller
            )
        elif Company.is_user_company(request.user):
            form = CompanyUpdateForm(
                request.POST, 
                request.FILES, 
                instance=request.user.company
            )
            
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        if Seller.is_user_seller(request.user):
            form = SellerUpdateForm(instance=request.user.seller)
        elif Company.is_user_company(request.user):
            form = CompanyUpdateForm(instance=request.user.company)
        else:
            messages.error(request, 'Invalid user type')
            return redirect('home')
            
    return render(request, 'MainApp/profile.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'MainApp/login.html')


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('home')

    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('home')
   
@login_required
def seller_dashboard(request):
    try:
        seller = Seller.objects.get(user=request.user)
        seller_materials = seller.materials.all()
        
        # Get full company details including email
        matching_companies = Company.objects.filter(
            required_materials__in=seller_materials
        ).distinct().select_related('user').prefetch_related('required_materials').values(
            'user__username',
            'user__email',
            'user',  
            'address',
            'phone',
            'website',
            'Main_product',
            'required_materials__name'  # Get material names instead of IDs
        )[:10]  # Limit to top 10

        company_details = {}
        for company in matching_companies:
            user_id = company['user']
            if user_id not in company_details:
                company_details[user_id] = {
                    'username': company['user__username'],
                    'email': company['user__email'],
                    'address': company['address'],
                    'phone': company['phone'],
                    'website': company['website'],
                    'main_product': company['Main_product'],
                    'required_materials': set()
                }
                company_details[user_id]['required_materials'].add(company['required_materials__name'])

        # Convert sets to lists for JSON serialization
        for details in company_details.values():
            details['required_materials'] = list(details['required_materials'])

        matching_companies = list(company_details.values())
        
        context = {
            'matching_companies': matching_companies,
            'seller_materials': seller_materials,
            'seller_email': seller.user.email
        }
        
        return render(request, 'MainApp/company_search.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, "Seller account required.")
        return redirect('home')