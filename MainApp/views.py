from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View
from .forms import SellerRegistrationForm, CompanyRegistrationForm, SellerUpdateForm, CompanyUpdateForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Seller, Company, SellerMaterialInventory, Material
import csv
import pandas as pd
from django.contrib.auth.models import User
from django.db import transaction

"""
██╗  ██╗ ██████╗ ███╗   ███╗███████╗    ██████╗  █████╗  ██████╗ ███████╗
██║  ██║██╔═══██╗████╗ ████║██╔════╝    ██╔══██╗██╔══██╗██╔════╝ ██╔════╝
███████║██║   ██║██╔████╔██║█████╗      ██████╔╝███████║██║  ███╗█████╗  
██╔══██║██║   ██║██║╚██╔╝██║██╔══╝      ██╔═══╝ ██╔══██║██║   ██║██╔══╝  
██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗    ██║     ██║  ██║╚██████╔╝███████╗
╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
A beautifully designed landing page that serves as the entry point to our application.
This view renders the main index template that welcomes users to our platform.
Returns:
    HttpResponse: Renders the 'MainApp/index.html' template, providing users with
    their first glimpse of our application's interface and functionality.
"""  

def home(request):
    return render(request, 'MainApp/index.html')


"""
██╗      ██████╗  ██████╗ ██╗███╗   ██╗    ███████╗██╗ ██████╗ ███╗   ██╗██╗   ██╗██████╗ 
██║     ██╔═══██╗██╔════╝ ██║████╗  ██║    ██╔════╝██║██╔════╝ ████╗  ██║██║   ██║██╔══██╗
██║     ██║   ██║██║  ███╗██║██╔██╗ ██║    ███████╗██║██║  ███╗██╔██╗ ██║██║   ██║██████╔╝
██║     ██║   ██║██║   ██║██║██║╚██╗██║    ╚════██║██║██║   ██║██║╚██╗██║██║   ██║██╔═══╝ 
███████╗╚██████╔╝╚██████╔╝██║██║ ╚████║    ███████║██║╚██████╔╝██║ ╚████║╚██████╔╝██║     
╚══════╝ ╚═════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝    ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝     
Authentication Views Module
This module handles user authentication including signup, login and logout functionality.
It contains the following key views:
signup_view:
    Handles new user registration for both sellers and companies
    - Validates and processes registration forms
    - Creates user accounts and associated profiles
    - Handles profile picture uploads
    - Associates companies with their required materials
login_view:
    Manages user authentication
    - Validates credentials
    - Creates user sessions
    - Redirects to home page on success
LogoutView:
    Class-based view for user logout
    - Terminates user sessions
    - Supports both GET and POST requests
    - Redirects to home page
Key Features:
- Secure password handling
- Form validation with error messages
- Profile picture upload support
- Role-based registration (Seller/Company)
- Material selection for companies
- Session management
- Clean error handling
Dependencies:
    django.contrib.auth - For core authentication
    django.contrib.messages - For user feedback
    Custom Forms - SellerRegistrationForm, CompanyRegistrationForm
    Custom Models - Seller, Company, Material
"""

def signup_view(request):
    seller_form = SellerRegistrationForm()
    company_form = CompanyRegistrationForm()

    if request.method == 'POST':
        role = request.POST.get('role')
        selected_materials = []
        if role == 'seller':
            form = SellerRegistrationForm(request.POST, request.FILES)
            seller_form = form
            if form.is_valid():
                try:
                    user = form.save(commit=False)  # Don't save to DB yet
                    user.save()  # Now save user
                    
                    # Create seller profile
                    seller = Seller.objects.create(
                        user=user,
                        phone=form.cleaned_data['phone'],
                        profile_picture=form.cleaned_data.get('profile_picture'),
                        address=form.cleaned_data['address'],
                        whatsapp_number=form.cleaned_data['whatsapp_number']
                    )
                    login(request, user)
                    messages.success(request, 'Seller account created successfully!')
                    return redirect('home')
                except Exception as e:
                    print(e)
                    messages.error(request, f'Error creating seller account: {str(e)}')
        
        elif role == 'company':
            for material in request.POST.getlist('selected_materials', []):
                selected_materials.extend(int(id) for id in material.split(','))
            form = CompanyRegistrationForm(request.POST, request.FILES)
            company_form = form
            if form.is_valid():
                try:
                    user = form.save(commit=False)  # Don't save to DB yet
                    user.save()  # Now save user
                    
                    # Create company profile
                    company = Company.objects.create(
                        user=user,
                        phone=form.cleaned_data['phone'],
                        address=form.cleaned_data['address'],
                        country=form.cleaned_data['country'],
                        website=form.cleaned_data['website'],
                        Main_product=form.cleaned_data['Main_product']
                    )
                    
                    # Add selected materials
                    if selected_materials:
                        materials = Material.objects.filter(id__in=selected_materials)
                        company.required_materials.set(materials)
                    
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

    context = {
        'seller_form': seller_form,
        'company_form': company_form,
        'materials': Material.objects.all(),
    }
    return render(request, 'MainApp/signup.html', context)

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
    
def get_materials(request):
    category = request.GET.get('category', 'all')
    search = request.GET.get('search', '')
    
    materials = Material.objects.all()
    
    if search:
        materials = materials.filter(name__icontains=search)
    if category != 'all':
        materials = materials.filter(category=category)
        
    return JsonResponse({
        'materials': list(materials.values('id', 'name')[:100])  # Limit to 100 results
    })


"""
Profile Views Module
This module handles user profile management for both sellers and companies.
It contains the following key views:
profile_view:
    Displays and updates user profile information
    - Handles profile updates for sellers and companies
    - Supports profile picture uploads
    - Provides feedback on successful updates
    - Redirects to home page on success
seller_dashboard:
    Displays a list of companies matching a seller's available materials
    - Fetches seller's materials from inventory
    - Retrieves matching companies based on inventory materials
    - Displays company details and required materials
    - Supports seller email retrieval
"""    

@login_required
def profile_view(request):
    """
    Display and update user profile.
    """
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

   
@login_required
def seller_dashboard(request):
    try:
        seller = Seller.objects.get(user=request.user)
        # Get seller's materials from inventory
        seller_inventory = SellerMaterialInventory.objects.filter(seller=seller)
        seller_materials = [inventory.material for inventory in seller_inventory]
        
        # Get matching companies based on inventory materials
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
            'required_materials__name'
        )[:10]

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
            'seller_materials': seller_materials,  # Now contains materials from inventory
            'seller_email': seller.user.email
        }
        
        return render(request, 'MainApp/company_search.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, "Seller account required.")
        return redirect('home')
   

#**************************************************************************#
#*                                                                        *#
#*                       AUTOMATION ZONE                                  *#
#*                                                                        *#
#*     ____________________________________________________             *#
#*                                                                        *#
#*     Auto-filling company data from Excel/CSV files                    *#
#*     Handles bulk processing of company information                    *#
#*     Creates users, companies, and material relationships              *#
#*     Efficient database operations using transactions                  *#
#*                                                                        *#
#*     WARNING: This section contains automated data processing          *#
#*     Make sure input files follow the required format                  *#
#*                                                                        *#
#**************************************************************************#

def fill(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
                processed = update_company_data(df)
                messages.success(request, f'Successfully processed {processed} companies from CSV!')
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
                processed = update_company_data(df)
                messages.success(request, f'Successfully processed {processed} companies from Excel!')
            else:
                messages.error(request, 'Invalid file format. Please upload .csv, .xls, or .xlsx file.')
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
    
    return render(request, 'MainApp/fill.html')

@transaction.atomic
def update_company_data(df):
    # Process materials first
    if 'Ingredients' in df.columns:
        all_ingredients = set()
        for ingredients in df['Ingredients'].dropna():
            ingredients_list = [ing.strip() for ing in str(ingredients).split(',')]
            all_ingredients.update(ing for ing in ingredients_list if ing)
        
        # Bulk create materials
        existing_materials = set(Material.objects.values_list('name', flat=True))
        new_materials = [Material(name=name) for name in all_ingredients if name not in existing_materials]
        Material.objects.bulk_create(new_materials, ignore_conflicts=True)
    
    # Prepare bulk lists
    users_to_create = []
    companies_to_create = []
    materials_mapping = {}
    
    # Create mapping of material names to objects
    all_materials = {m.name: m for m in Material.objects.all()}
    
    # Collect all user and company data
    existing_usernames = set(User.objects.values_list('username', flat=True))
    
    for _, row in df.iterrows():
        original_username = str(row.get('Company_Name', '')).strip()
        if original_username:
            # Handle duplicate usernames
            username = original_username
            counter = 1
            while username in existing_usernames:
                username = f"{original_username}_{counter}"
                counter += 1
            
            # Prepare user data
            user = User(
                username=username,
                email=str(row.get('Company_email', '')).strip(),
            )
            existing_usernames.add(username)
            user.set_password('Pande@123')
            users_to_create.append(user)
            
            # Prepare company data
            address = str(row.get('Company_address', '')).strip()
            address_parts = address.split()
            country = address_parts[-1] if address_parts else ''
            address = ' '.join(address_parts[:-1]) if address_parts else ''
            
            phone = str(row.get('Company_phone', '')).replace('+', '').replace('(', '').replace(')', '').replace(' ', '')
            
            company = Company(
                user=user,  # Will be updated after bulk_create
                phone=phone,
                address=address,
                country=country,
                website=str(row.get('Company_URL', '')).strip(),
                Main_product="Default Product"
            )
            companies_to_create.append(company)
            
            # Store materials for this company
            if 'Ingredients' in df.columns:
                ingredients = [ing.strip() for ing in str(row.get('Ingredients', '')).split(',') if ing.strip()]
                materials_mapping[username] = [all_materials[ing] for ing in ingredients if ing in all_materials]

    # Bulk create users
    User.objects.bulk_create(users_to_create)
    
    # Update company user references
    username_to_user = {u.username: u for u in User.objects.filter(username__in=[c.username for c in users_to_create])}
    for company in companies_to_create:
        company.user = username_to_user[company.user.username]
    
    # Bulk create companies
    Company.objects.bulk_create(companies_to_create)
    
    # Bulk create material relationships
    through_model = Company.required_materials.through
    material_relations = []
    
    for company in Company.objects.filter(user__username__in=materials_mapping.keys()):
        for material in materials_mapping.get(company.user.username, []):
            material_relations.append(
                through_model(company_id=company.id, material_id=material.id)
            )
    
    through_model.objects.bulk_create(material_relations)
    
    return len(users_to_create)
