from rest_framework import serializers
from .models import Entry, Company
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']


class EntrySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Nest the user details

    class Meta:
        model = Entry
        fields = '__all__'
        read_only_fields = ['entry_status', 'updated_at']

    def validate(self, data):
        user_role = self.context['request'].user.role
        if user_role == 'accountant':
            data['entry_status'] = 'pending'  # Set default status for accountant-created entries
        return data
    

class CreateCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

