from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, parser_classes, permission_classes,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Profile, User
from .serializers import LoginSerializer, ProfileSerializer, RegisterSerializer, UserSummarySerializer


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def api_csrf(request):
    return Response({'csrfToken': get_token(request)})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_protect
def api_register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'status': False, 'message': 'Data registrasi tidak valid.',
                         'errors': serializer.errors}, status=400)
    user = serializer.save()
    return Response({'status': True, 'message': 'Registrasi berhasil.',
                     'user': UserSummarySerializer(user).data}, status=201)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_protect
def api_login(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'status': False, 'message': 'Data login tidak valid.',
                         'errors': serializer.errors}, status=400)
    identifier = serializer.validated_data['identifier']
    username = identifier
    if '@' in identifier:
        user = User.objects.filter(email__iexact=identifier).first()
        if user:
            username = user.username
    user = authenticate(request, username=username, password=serializer.validated_data['password'])
    if user is None:
        return Response({'status': False, 'message': 'Kredensial tidak valid.'}, status=401)
    login(request, user)
    profile, _ = Profile.objects.get_or_create(user=user)
    return Response({
        'status': True, 'message': 'Login berhasil.',
        'user': UserSummarySerializer(user).data,
        'profile': ProfileSerializer(profile, context={'request': request}).data,
        'csrfToken': get_token(request),
    })


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_logout(request):
    username = request.user.username
    logout(request)
    return Response({'status': True, 'message': f'Logout berhasil untuk {username}.'})


@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def api_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'GET':
        return Response({'status': True, 'profile': ProfileSerializer(
            profile, context={'request': request},
        ).data})
    serializer = ProfileSerializer(
        profile, data=request.data, partial=request.method == 'PATCH', context={'request': request},
    )
    if not serializer.is_valid():
        return Response({'status': False, 'message': 'Data profil tidak valid.',
                         'errors': serializer.errors}, status=400)
    serializer.save()
    return Response({'status': True, 'message': 'Profil berhasil diperbarui.', 'profile': serializer.data})
