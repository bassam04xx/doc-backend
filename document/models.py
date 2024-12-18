from django.db import models
from user.models import User

class Document(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    category = models.CharField(max_length=255)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_documents')
    summary = models.TextField()
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50)

    def __str__(self) -> str:
        # Dynamically list all fields and their values
        field_values = []
        for field in self._meta.get_fields():
            if field.concrete:  # Skip related fields like reverse relationships
                field_name = field.name
                field_value = getattr(self, field_name, None)
                field_values.append(f"{field_name}: {field_value}")
        return ", ".join(field_values)

        

    class Meta:
        db_table = 'documents'  # Replace with your preferred table name