from rest_framework import serializers

from userman.models import User


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["name", "username", "email", "phone_number", "password"]

    def create(self, validated_data):
        instance = User()
        instance.name = validated_data['name']
        instance.username = validated_data["username"]
        instance.email = validated_data.get('email')
        instance.phone_number = validated_data['phone_number']
        instance.set_password(validated_data.get('password') or None)
        instance.save()
        return instance


class UserDetailsSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source='id', read_only=True)

    class Meta:
        model = User
        fields = ["user_id", "name", "username", "phone_number"]
