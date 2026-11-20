from django.db import transaction
from rest_framework import serializers

from .forms import ProfileForm, RegisterForm
from .models import Profile, User


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False, required=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False, required=False)
    password1 = serializers.CharField(write_only=True, trim_whitespace=False, required=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False, required=False)
    full_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate(self, attrs):
        password = attrs.get('password', attrs.get('password1', ''))
        confirm = attrs.get('password_confirm', attrs.get('password2', password))
        form = RegisterForm(data={
            'username': attrs['username'], 'email': attrs['email'],
            'password1': password, 'password2': confirm,
        })
        if not form.is_valid():
            raise serializers.ValidationError(dict(form.errors))
        if User.objects.filter(username__iexact=form.cleaned_data['username']).exists():
            raise serializers.ValidationError({'username': ['Username sudah terdaftar.']})
        full_name = ' '.join(attrs.get('full_name', '').split())
        if full_name and len(full_name) < 2:
            raise serializers.ValidationError({'full_name': ['Nama lengkap terlalu pendek.']})
        return {
            'username': form.cleaned_data['username'],
            'email': form.cleaned_data['email'],
            'password': password, 'full_name': full_name,
        }

    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop('full_name')
        user = User.objects.create_user(**validated_data)
        profile, _ = Profile.objects.get_or_create(user=user)
        if full_name:
            profile.full_name = full_name
            profile.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        identifier = attrs.get('username') or attrs.get('email')
        if not identifier:
            raise serializers.ValidationError('Username/email dan password wajib diisi.')
        attrs['identifier'] = identifier
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    whatsapp_link = serializers.CharField(read_only=True)
    whatsapp = serializers.CharField(max_length=20, required=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'email', 'full_name', 'faculty', 'angkatan',
            'whatsapp', 'line_id', 'photo', 'is_complete', 'whatsapp_link', 'updated_at',
        ]
        read_only_fields = ['id', 'username', 'email', 'is_complete', 'whatsapp_link', 'updated_at']

    def validate(self, attrs):
        # Reuse the web form so both interfaces share validation and normalization.
        data = {field: value for field, value in attrs.items() if field != 'photo'}
        files = {'photo': attrs['photo']} if attrs.get('photo') else None
        form = ProfileForm(data=data, files=files, instance=self.instance)
        # An incomplete profile may be filled one field at a time with PATCH.
        if self.partial:
            for field in list(form.fields):
                if field not in attrs:
                    del form.fields[field]
        if not form.is_valid():
            raise serializers.ValidationError(dict(form.errors))
        return {field: form.cleaned_data[field] for field in attrs}
