from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Seller, Company,Material
from django.core.validators import RegexValidator
from django.contrib.auth.forms import UserChangeForm

class SellerRegistrationForm(UserCreationForm):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'required': True
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'required': True
        })
    )
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profile_picture = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))
    whatsapp_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone', 'profile_picture', 'address', 'whatsapp_number']

    def save(self, commit=True):
        from django.db import transaction
        
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            try:
                with transaction.atomic():
                    user.save()
                    seller = Seller.objects.create(
                        user=user,
                        phone=self.cleaned_data['phone'],
                        profile_picture=self.cleaned_data['profile_picture'],
                        address=self.cleaned_data['address'],
                        whatsapp_number=self.cleaned_data['whatsapp_number']
                    )
                    if 'materials' in self.cleaned_data:
                        seller.materials.set(self.cleaned_data['materials'])
                    seller.save()
            except Exception as e:
                if user.pk:
                    user.delete()
                raise e
        return user
    
class CompanyRegistrationForm(UserCreationForm):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'required': True
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'required': True
        })
    )
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))
    country = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    website = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    Main_product = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone', 'address', 'country', 'website', 'Main_product']

    def save(self, commit=True):
        from django.db import transaction
        
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            try:
                with transaction.atomic():
                    user.save()
                    company = Company.objects.create(
                        user=user,
                        phone=self.cleaned_data['phone'],
                        address=self.cleaned_data['address'],
                        country=self.cleaned_data['country'],
                        website=self.cleaned_data['website'],
                        Main_product=self.cleaned_data['Main_product'],
                        required_materials=self.cleaned_data['required_materials']
                    )
                    company.save()
            except Exception as e:
                if user.pk:
                    user.delete()
                raise e
        return user
    
class SellerUpdateForm(forms.ModelForm):
    """
    Custom form for updating seller profile information.
    """
    phone = forms.CharField(
        max_length=20, 
        validators=[
            RegexValidator(
                r'^\+?1?\d{9,15}$', 
                'Enter a valid phone number, including country code.'
            )
        ],
        required=False,
        help_text="Optional. Update your phone number.",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )
    whatsapp_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Seller
        fields = ['phone', 'profile_picture', 'address', 'whatsapp_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['phone'].initial = self.instance.phone
            self.fields['profile_picture'].initial = self.instance.profile_picture
            self.fields['address'].initial = self.instance.address
            self.fields['whatsapp_number'].initial = self.instance.whatsapp_number

class CompanyUpdateForm(forms.ModelForm):
    """
    Custom form for updating company profile information.
    """
    phone = forms.CharField(
        max_length=20, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )
    country = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    Main_product = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Company
        fields = ['phone', 'address', 'country', 'website', 'Main_product']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['phone'].initial = self.instance.phone
            self.fields['address'].initial = self.instance.address
            self.fields['country'].initial = self.instance.country
            self.fields['website'].initial = self.instance.website
            self.fields['Main_product'].initial = self.instance.Main_product
