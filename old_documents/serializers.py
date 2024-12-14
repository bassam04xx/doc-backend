from rest_framework import serializers
from .models import OldDocument

class OldDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OldDocument
        fields = '__all__'
