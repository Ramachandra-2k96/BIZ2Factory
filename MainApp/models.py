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
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    address = models.TextField(null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)

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
        Returns a list of company names where the company's required materials match the seller's available materials.
        """
        seller_materials = SellerMaterialInventory.objects.filter(seller=self).select_related('material')
        
        matching_companies = Company.objects.filter(
            required_materials__in=[inventory.material for inventory in seller_materials]
        ).distinct()
        
        return [company.user.username for company in matching_companies]

class SellerMaterialInventory(models.Model):
    """Track the quantity of each material a seller has."""
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.seller.user.username} has {self.quantity} of {self.material.name}"

class TransactionHistory(models.Model):
    """Track changes in material quantities for sellers."""
    seller_material_inventory = models.ForeignKey(SellerMaterialInventory, on_delete=models.CASCADE)
    change = models.IntegerField()  # Positive for addition, negative for subtraction
    date = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, null=True, blank=True)  # Optional note to describe the transaction

    def __str__(self):
        return f"{self.seller_material_inventory.seller.user.username} changed {self.seller_material_inventory.material.name} by {self.change} on {self.date}"
    
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
