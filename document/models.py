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
        return self.file_name

    class Meta:
        db_table = 'document'  # Replace with your preferred table name