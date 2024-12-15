from django.db import models

class OldDocument(models.Model):
    id = models.AutoField(primary_key=True)  # Primary key
    user_id = models.IntegerField()         # User ID field
    category = models.CharField(max_length=255)  # Category as a string
    filename = models.CharField(max_length=255)  # Filename
    created_at = models.DateTimeField()     # Timestamp of creation
    status = models.CharField(max_length=255, default='pending')  # Status of the document

    class Meta:
        db_table = 'old_documents'  # Name of the old table
