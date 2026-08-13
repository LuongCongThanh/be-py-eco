"""Supported Country — guild.md §3.2. Vietnam-only at launch; full
Master-Admin-configurable multi-country support is Slice 11's job, not
this slice's (Issue #6 "Out of Scope").
"""

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django_countries.fields import CountryField

from common.db.models import BaseModel


class SupportedCountry(BaseModel):
    code = CountryField(unique=True)
    name = models.CharField(max_length=100)
    default_locale = models.CharField(max_length=10)
    allowed_locales = ArrayField(models.CharField(max_length=10))
    allowed_currencies = ArrayField(models.CharField(max_length=3))
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "localization_supported_country"

    def __str__(self) -> str:
        return str(self.code)
