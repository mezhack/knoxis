from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Organization, OrganizationMember, User


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "city", "state"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]


class SignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    organization = serializers.DictField()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este email já está em uso.")
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_organization(self, value):
        required = ["name", "slug"]
        for field in required:
            if not value.get(field):
                raise serializers.ValidationError(f"Campo '{field}' obrigatório.")
        if Organization.objects.filter(slug=value["slug"]).exists():
            raise serializers.ValidationError("Este slug já está em uso.")
        return value

    def create(self, validated_data):
        org_data = validated_data.pop("organization")
        user = User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            password=validated_data["password"],
        )
        org = Organization.objects.create(**org_data)
        OrganizationMember.objects.create(organization=org, user=user, role="owner")
        return user, org


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            request=self.context.get("request"),
            username=data["email"].lower(),
            password=data["password"],
        )
        if user is None:
            raise serializers.ValidationError("Email ou senha inválidos.")
        if not user.is_active:
            raise serializers.ValidationError("Conta desativada.")
        data["user"] = user
        return data
