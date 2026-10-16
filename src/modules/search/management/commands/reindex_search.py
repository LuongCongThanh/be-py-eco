from django.core.management.base import BaseCommand

from modules.search.services.reindex import reindex_all


class Command(BaseCommand):
    help = "Rebuild the OpenSearch product index from PostgreSQL (guild.md §15 Slice 3, commit 6)."

    def handle(self, *args, **options) -> None:
        count = reindex_all()
        self.stdout.write(self.style.SUCCESS(f"Reindexed {count} published Product(s)."))
