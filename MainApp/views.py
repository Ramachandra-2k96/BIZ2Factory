from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View
from .forms import SellerRegistrationForm, CompanyRegistrationForm, SellerUpdateForm, CompanyUpdateForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Seller, Company, SellerMaterialInventory, Material, TransactionHistory
import csv
import pandas as pd
from django.contrib.auth.models import User
from django.db import transaction
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv('BREVO_API_KEY')

# Configure the API client
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = API_KEY
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


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
        
        # Get companies that need ANY of the seller's materials (OR condition)
        matching_companies = Company.objects.filter(
            required_materials__in=seller_materials  # This creates an OR condition
        ).distinct().select_related('user').prefetch_related('required_materials')
        
        company_list = []
        for company in matching_companies:
            # Get all required materials for this company
            required_materials = list(company.required_materials.all().values_list('name', flat=True))
            
            # Get matching materials (intersection between seller's and company's materials)
            matching_materials = [m.name for m in seller_materials if m.name in required_materials]
            
            company_info = {
                'id': company.id,
                'username': company.user.username,
                'email': company.user.email,
                'address': company.address,
                'phone': company.phone,
                'website': company.website,
                'main_product': company.Main_product,
                'required_materials': required_materials,
                'matching_materials': matching_materials  # Add matching materials to context
            }
            company_list.append(company_info)

        context = {
            'matching_companies': company_list,
            'seller_materials': [m.name for m in seller_materials],
            'seller_email': seller.user.email
        }
        
        return render(request, 'MainApp/company_search.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, "Seller account required.")
        return redirect('home')
   
@login_required
def add_inventory(request):
    if not Seller.is_user_seller(request.user):
        messages.error(request, "Only sellers can add inventory")
        return redirect('profile')
        
    if request.method == 'POST':
        material_id = request.POST.get('material')
        quantity = request.POST.get('quantity')
        available_from = request.POST.get('available_from')
        available_till = request.POST.get('available_till')
        
        try:
            material = Material.objects.get(id=material_id)
            seller = request.user.seller
            
            inventory = SellerMaterialInventory.objects.create(
                seller=seller,
                material=material,
                quantity=quantity,
                Available_from=available_from,
                Available_till=available_till
            )
            
            messages.success(request, f"Added {quantity} units of {material.name} to inventory")
            return redirect('profile')
            
        except Exception as e:
            messages.error(request, f"Error adding inventory: {str(e)}")
    
    materials = Material.objects.all()
    return render(request, 'MainApp/add_inventory.html', {'materials': materials})

@login_required
def inventory_management(request):
    if not Seller.is_user_seller(request.user):
        messages.error(request, "Only sellers can access inventory management")
        return redirect('profile')
    
    seller = request.user.seller
    inventory_items = SellerMaterialInventory.objects.filter(
        seller=seller
    ).select_related('material').prefetch_related('transactionhistory_set')
    
    transactions = TransactionHistory.objects.filter(
        seller_material_inventory__seller=seller
    ).order_by('-date')
    
    # Prepare data for chart
    chart_data = {}
    for transaction in transactions:
        date = transaction.date.strftime('%Y-%m-%d')
        material_name = transaction.seller_material_inventory.material.name
        if material_name not in chart_data:
            chart_data[material_name] = {'dates': [], 'quantities': []}
        chart_data[material_name]['dates'].append(date)
        chart_data[material_name]['quantities'].append(transaction.change)
    
    return render(request, 'MainApp/inventory_management.html', {
        'inventory_items': inventory_items,
        'transactions': transactions,
        'has_transactions': transactions.exists(),
        'chart_data': chart_data
    })

@login_required
def edit_inventory(request, inventory_id):
    inventory = get_object_or_404(SellerMaterialInventory, id=inventory_id, seller=request.user.seller)
    
    if request.method == 'POST':
        inventory.quantity = request.POST.get('quantity')
        inventory.Available_from = request.POST.get('available_from')
        inventory.Available_till = request.POST.get('available_till')
        inventory.save()
        messages.success(request, "Inventory updated successfully")
        return redirect('inventory_management')
        
    return render(request, 'MainApp/edit_inventory.html', {'inventory': inventory})

@login_required
def delete_inventory(request, inventory_id):
    if not request.user.is_authenticated or not hasattr(request.user, 'seller'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'})
        
    try:
        inventory = SellerMaterialInventory.objects.get(
            id=inventory_id, 
            seller=request.user.seller
        )
        inventory.delete()
        return JsonResponse({'status': 'success'})
    except SellerMaterialInventory.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Inventory not found'})


def send_email(to_email, subject, html_content, from_name, from_email):
    """
    Send a simple email using the Brevo Transactional Email API.

    Args:
        to_email (str): The recipient's email address.
        subject (str): The subject of the email.
        html_content (str): The HTML content of the email.
        from_name (str): The sender's name.
        from_email (str): The sender's email address.
    
    Returns:
        Response: API response from Brevo.
    """
    try:
        # Prepare the email data
        email_data = {
            "sender": {"name": from_name, "email": from_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content
        }

        # Send the email using the TransactionalEmailsApi
        api_response = api_instance.send_transac_email(email_data)
        pprint(api_response)
        return api_response
    except ApiException as e:
        print(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")
        return None

@login_required
def contact_company(request, company_id):
    """Send email to a single company"""
    if not request.method == 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    try:
        seller = Seller.objects.get(user=request.user)
        company = Company.objects.get(id=company_id)
        
        # Get seller's materials that match company's requirements
        seller_inventory = SellerMaterialInventory.objects.filter(
            seller=seller,
            material__in=company.required_materials.all()
        )
        
        matching_materials = [inv.material.name for inv in seller_inventory]
        
        html_content = f"""
        <h2>Material Supply Interest</h2>
        <p>Hello {company.user.username},</p>
        <p>{seller.user.username} is interested in supplying materials to your company.</p>
        <p>Matching materials available:</p>
        <ul>
            {''.join(f'<li>{material}</li>' for material in matching_materials)}
        </ul>
        <p>Contact details:</p>
        <p>Email: {seller.user.email}</p>
        <p>Phone: {seller.phone}</p>
        """
        
        response = send_email(
            to_email=company.user.email,
            subject="Material Supply Interest",
            html_content=html_content,
            from_name=seller.user.username,
            from_email=seller.user.email
        )
        
        if response:
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Failed to send email'})
        
    except (Seller.DoesNotExist, Company.DoesNotExist) as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def notify_top_companies(request):
    """Send email to top 10 matching companies"""
    if not request.method == 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    try:
        seller = Seller.objects.get(user=request.user)
        seller_materials = SellerMaterialInventory.objects.filter(
            seller=seller,
            quantity__gt=0
        ).values_list('material', flat=True)
        
        matching_companies = Company.objects.filter(
            required_materials__in=seller_materials
        ).distinct()[:10]
        
        success_count = 0
        for company in matching_companies:
            matching_materials = company.required_materials.filter(
                id__in=seller_materials
            )
            
            html_content = f"""
            <h2>Material Supply Availability</h2>
            <p>Hello {company.user.username},</p>
            <p>{seller.user.username} has materials that match your requirements:</p>
            <ul>
                {''.join(f'<li>{material.name}</li>' for material in matching_materials)}
            </ul>
            <p>Contact details:</p>
            <p>Email: {seller.user.email}</p>
            <p>Phone: {seller.phone}</p>
            """
            
            response = send_email(
                to_email=company.user.email,
                subject="Material Supply Match",
                html_content=html_content,
                from_name=seller.user.username,
                from_email=seller.user.email
            )
            
            if response:
                success_count += 1
        
        return JsonResponse({
            'status': 'success',
            'message': f'Successfully sent emails to {success_count} companies'
        })
        
    except Seller.DoesNotExist as e:
        return JsonResponse({'status': 'error', 'message': str(e)})   
    
    
    
    
    
    
    
    
    
    
    
    
    
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
