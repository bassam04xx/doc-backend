class OldDatabaseRouter:
    """
    A router to control all database operations for the OldDocument model.
    """

    def db_for_read(self, model, **hints):
        """Point all read operations for OldDocument to old_db."""
        if model._meta.db_table == 'old_documents':
            return 'old_db'
        return None

    def db_for_write(self, model, **hints):
        """Point all write operations for OldDocument to old_db."""
        if model._meta.db_table == 'old_documents':
            return 'old_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations only if both models are in the old_db."""
        if (
            obj1._meta.db_table == 'old_documents'
            or obj2._meta.db_table == 'old_documents'
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure migrations for OldDocument are applied only on old_db."""
        if model_name == 'olddocument':
            return db == 'old_db'
        return None
