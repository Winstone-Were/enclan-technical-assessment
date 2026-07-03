from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password, password_validators_help_texts
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        help_text=password_validators_help_texts(),
        style={'input_type','password'},
    )

    class Meta:
        model = User
        fields = ['username','email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email',''),
            password=validated_data['password']
        )
    
    