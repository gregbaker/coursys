class DatabaseRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == "postgres_fts_backend":
            return "fts"
        return None
    
    def db_for_write(self, model, **hints):
        if model._meta.app_label == "postgres_fts_backend":
            return "fts"
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        print(f"################allow_relation {obj1.model} {obj2.model}\n")
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "postgres_fts_backend":
            return db == "fts"
        return None