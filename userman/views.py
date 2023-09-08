from django.http import JsonResponse
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes

from .serializers import UserCreateSerializer, UserDetailsSerializer
from rest_framework import status


# Ideally we should rate-limit this
@api_view(['POST'])
def register_user(request) -> JsonResponse:
    # Validating the request.
    serializer = UserCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return JsonResponse(
            {'message': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer.save()
    read_serializer = UserDetailsSerializer(instance=serializer.instance)
    return JsonResponse(read_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
def get_user_details(request) -> JsonResponse:
    # Validating the request.
    serializer = UserDetailsSerializer(instance=request.user)
    return JsonResponse(serializer.data, status=status.HTTP_200_OK)
