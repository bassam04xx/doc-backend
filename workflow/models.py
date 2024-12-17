from django.db import models
from user.models import User

class Workflow(models.Model):
    document = models.ForeignKey('document.Document', on_delete=models.CASCADE)
    former_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Add this line

    def __str__(self) -> str:
        return self.document.file_name

    class Meta:
        db_table = 'workflow'