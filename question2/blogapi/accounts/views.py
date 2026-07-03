from rest_framework import status
from rest_framework import serializers as drf_serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer

from .serializers import RegisterSerializer


@extend_schema(
    request=RegisterSerializer,
    responses={201: None, 400: None},
        description=(
        "Create a new user account.\n\n"
        "**Password rules:** minimum 8 characters, not entirely numeric, "
        "not a common password, not too similar to the username or email. "
        "Violations return 400 with per-rule error messages."
    ),
    examples=[
        OpenApiExample(
            'Valid registration',
            value={
                "username": "string",
                "email": "string",
                "password": "string"
            },
            request_only=True,   # show this example for the request body only
        ),
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"detail": "Account Created."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        name='LogoutRequest',
        fields={'refresh': drf_serializers.CharField()}
    ),
    responses={205: None, 400: None},
    description="Logout: blacklists the refresh token so it can't be reused."
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        token = RefreshToken(request.data["refresh"])
        token.blacklist()
        return Response({"detail": "Logged out."}, status=status.HTTP_205_RESET_CONTENT)
    except KeyError:
        return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    responses={204: None},
    description="Delete the authenticated user's own account (and their posts, via cascade)."
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    request.user.delete()                                          # ← fixed typo
    return Response({"detail": "Account deleted."}, status=status.HTTP_204_NO_CONTENT)   # ← fixed message