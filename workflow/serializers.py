from rest_framework import serializers
from .models import Workflow
from user.models import User  # Adjust the import based on the actual location of your User model

class WorkflowSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = ['id', 'document', 'former_status', 'new_status', 'updated_at', 'updated_by_username']

    def get_updated_by_username(self, obj):
        try:
            return obj.updated_by.username  # Assuming `username` is the field you want on the User model
        except User.DoesNotExist:
            return None