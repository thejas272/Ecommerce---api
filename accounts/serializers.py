from rest_framework import serializers
from accounts import models
from django.db import IntegrityError
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
import re


class RegsiterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, max_length=30)
    last_name  = serializers.CharField(required=True, max_length=30)
    username   = serializers.CharField(required=True, max_length=30)
    password   = serializers.CharField(required=True, write_only=True, min_length=8)
    email      = serializers.EmailField(required=True)

    class Meta:
        model = models.User
        fields = ["first_name","last_name","username","password","email"]
    
    def validate_first_name(self, value):
        if not re.fullmatch(r"[A-Za-z]+",value):
            raise serializers.ValidationError("First name must only contain letters.")
        return value
    
    def validate_last_name(self, value):
        if not re.fullmatch(r"[A-Za-z]+( [A-Za-z]+)*", value.strip()):
            raise serializers.ValidationError("Last name must only contain letters and spaces.")
        return value
    
    def validate_username(self, value):
        if not re.match(r'^[A-Za-z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores.")
        
        if models.User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        
        return value
    

    def validate_email(self, value):
        value = value.lower()
        if models.User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already taken.")
        
        return value

    
    def validate(self, attrs):
        return attrs
    


    def create(self, validated_data):

        try:
            user = models.User.objects.create_user(first_name = validated_data['first_name'],
                                                   last_name  = validated_data['last_name'],
                                                   username   = validated_data['username'],
                                                   password   = validated_data['password'],
                                                   email      = validated_data['email'],
                                                   )
            return user
        
        except IntegrityError:
            raise serializers.ValidationError({"detail":"Username or email already taken."})
        



    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        
        attrs["user"] = user
        
        return attrs



class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        token = attrs.get("refresh")

        try:
            self.token = RefreshToken(token)
        except TokenError:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        
        if self.token.token_type != "refresh":
            raise serializers.ValidationError("Invalid token type.")
        
        return attrs
    
    def save(self, **kwargs):
        self.token.blacklist()




class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

    def validate(self, attrs):

        token = attrs.get('refresh')

        try:
            refresh = RefreshToken(token)
        except TokenError:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        
        if refresh.token_type != "refresh":
            raise serializers.ValidationError("Invalid token type.")
        
        user_id = refresh.get("user_id")

        try:
            user = models.User.objects.get(id=user_id)
        except models.User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")
        
        attrs["refresh_token"] = refresh
        
        return attrs
    
