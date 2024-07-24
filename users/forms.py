from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms

from django.contrib.auth import get_user_model
from entries.models import Company


User = get_user_model()

class CustomUserInitialCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    company = forms.ModelMultipleChoiceField(
        queryset=Company.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'}),
        required=True
    )
    managers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='manager'),
        widget=forms.SelectMultiple(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'}),
        required=False
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'company', 'role', 'managers', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()  # Save the user first to generate an ID
        self.save_m2m()  # Save ManyToMany relationships after user is saved
        user.company.set(self.cleaned_data['company'])  # Assign companies to the user
        user.managers.set(self.cleaned_data['managers'])  # Assign managers to the user
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField()

class CustomUserEditForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:blue-500 focus:border-blue-500 sm:text-sm'}),
        required=False,
        help_text="Leave blank if you don't want to change the password.",
    )
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    company = forms.ModelMultipleChoiceField(
        queryset=Company.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'}),
        required=True
    )
    managers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='manager'),
        widget=forms.SelectMultiple(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role', 'company', 'managers', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        print(f'password in user form {password}')
        if password:
            user.set_password(password)
        else:
            user.password = User.objects.get(pk=user.pk).password
        if commit:
            user.save()
            self.save_m2m()  # Save ManyToMany relationships
        user.company.set(self.cleaned_data['company'])  # Assign companies to the user
        user.managers.set(self.cleaned_data['managers'])  # Assign managers to the user
        return user