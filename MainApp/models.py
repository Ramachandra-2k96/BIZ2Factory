from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

class Material(models.Model):
    """Material model to store product information."""
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Seller(models.Model):
    """
    Extended User model to include additional fields for user roles.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                r'^\+?1?\d{9,15}$',
                'Enter a valid phone number, including country code.'
            )
        ],
        blank=True,
        verbose_name="Phone Number"
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        verbose_name="Profile Picture",
        help_text="Optional profile picture for the user."
    )
    address = models.TextField(null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)
    materials = models.ManyToManyField(
        Material,
        related_name='sellers',
        blank=True
    )

    class Meta:
        permissions = [
            ("can_view_seller_details", "Can view seller details"),
        ]
    @property
    def is_seller(self):
        return True

    @classmethod
    def is_user_seller(cls, user):
        return hasattr(user, 'seller')
    
    def __str__(self):
        return self.user.username  
    
    def get_matching_companies(self):
        """
        Returns a list of company names where the company's required materials match the seller's materials.
        """
        seller_materials = self.materials.all()
        
        matching_companies = Company.objects.filter(required_materials__in=seller_materials).distinct()
        
        return [company.user.username for company in matching_companies]

class Company(models.Model):
    """
    Represents a company linked to sellers, suppliers, or companies.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    required_materials = models.ManyToManyField(Material, related_name='companies')
    Main_product = models.CharField(max_length=100, null=True, blank=True)

    @property
    def is_company(self):
        return True

    @classmethod 
    def is_user_company(cls, user):
        return hasattr(user, 'company')
    
    def __str__(self):
        return self.user.username
