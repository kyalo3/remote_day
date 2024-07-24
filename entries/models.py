from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = settings.AUTH_USER_MODEL

CURRENCY_OPTIONS = [
        ('INR', 'Rupee'),
        ('USD', 'Dollar'),
        ('EUR',  'Euro'),
        ('AED', 'Dirham'),
        ('AED', 'Riyal'),
    ]

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField((_('Company name')), max_length=255)
    currency = models.CharField(max_length=20, choices=CURRENCY_OPTIONS, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=False, null=True, blank=True)

    def __str__(self):
        return self.name

class Entry(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending'),
        ('manager_review_requested', 'Manager Review Requested'),
        ('manager_review_granted', 'Manager Review Granted')
    ]

    ENTRY_CHOICES = [
        ('receipt', 'Receipt'),
        ('payment', 'Payment')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    receipts = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    payments = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    currency = models.CharField(max_length=50, choices=CURRENCY_OPTIONS)
    date = models.DateField()    
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    entry_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    entry_type = models.CharField(max_length=30, choices=ENTRY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    from_excel = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, null=True)
    is_irregular = models.BooleanField(default=False)

    def __str__(self):
        return f"Entry {self.id} - {self.description[:20]}"
