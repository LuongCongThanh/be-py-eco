from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.search"
    label = "search"

    def ready(self) -> None:
        # Registers index_product as the handler for catalog's
        # ProductPublished outbox event — guild.md §15 Slice 3, commit 2.
        import modules.search.handlers  # noqa: F401
