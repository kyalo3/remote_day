from django import forms
from django.core.exceptions import ValidationError

from .models import Company, Entry, Category, Subcategory

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'currency']


class ReceiptForm(forms.ModelForm):

    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=True)
    subcategory = forms.ModelChoiceField(queryset=Subcategory.objects.none(), required=True)

    class Meta:
        model = Entry
        fields = ['currency', 'receipts', 'date', 'description', 'category', 'subcategory']

    def __init__(self, *args, company=None, is_irregular=False, **kwargs):
        self.company = company
        self.is_irregular = is_irregular
        self.user = kwargs.pop('user', None)
        super(ReceiptForm, self).__init__(*args, **kwargs)
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Subcategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
             self.fields['subcategory'].queryset = self.instance.category.subcategories.order_by('name')

        # Set default values to 0 if they are None or not provided
        if self.fields['receipts'].initial is None:
            self.fields['receipts'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        receipts = cleaned_data.get('receipts')

        # Ensure no negative values
        if receipts is not None and receipts < 0:
            self.add_error('receipts', 'Receipts cannot be negative.')

        # Ensure both are not zero
        if (receipts == 0 or receipts is None):
            raise ValidationError('Receipts Field cannot be zero.')

        return cleaned_data

    def save(self, commit=True, company=None, is_irregular=False):
        entry = super(ReceiptForm, self).save(commit=False)
        # Entry owner
        if self.user and self.user.role == 'accountant':
            entry.user = self.user
            entry.entry_type = 'receipt'
            if company:
                entry.company = company
            if is_irregular:
                entry.is_irregular = True

        if commit:
            entry.save()
        return entry
    

class PaymentForm(forms.ModelForm):

    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=True)
    subcategory = forms.ModelChoiceField(queryset=Subcategory.objects.none(), required=True)
    class Meta:
        model = Entry
        fields = ['currency', 'payments', 'date', 'description', 'category', 'subcategory']

    def __init__(self,  *args, company=None, is_irregular=False, **kwargs):
        self.company = company
        self.is_irregular = is_irregular
        self.user = kwargs.pop('user', None)
        super(PaymentForm, self).__init__(*args, **kwargs)
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Subcategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
             self.fields['subcategory'].queryset = self.instance.category.subcategories.order_by('name')

        # Set default values to 0 if they are None or not provided
        if self.fields['payments'].initial is None:
            self.fields['payments'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        payments = cleaned_data.get('payments')

        # Ensure no negative values
        if payments is not None and payments < 0:
            self.add_error('payments', 'Payments cannot be negative.')

        # Ensure both are not zero
        if (payments == 0 or payments is None):
            raise ValidationError('Payments Field cannot be zero.')

        return cleaned_data

    def save(self, commit=True, company=None, is_irregular=False):
        entry = super(PaymentForm, self).save(commit=False)
        # Entry owner
        if self.user and self.user.role == 'accountant':
            entry.user = self.user
            entry.entry_type = 'payment'
            if company:
                entry.company = company
            if is_irregular:
                entry.is_irregular = True

        if commit:
            entry.save()
        return entry
    
class ReceiptExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Upload Excel File')

class PaymentExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Upload Excel File')

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class SubcategoryForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=True)
    class Meta:
        model = Subcategory
        fields = ['name', 'category']
