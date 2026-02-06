#!/usr/bin/env python
"""Initialize default data for Binance Resender."""
import os


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binance_resender.settings')
    import django
    django.setup()

    from appSite.models import SenderLogManagerModel
    SenderLogManagerModel.objects.get_or_create(id=1, defaults={'use_log': 0})


if __name__ == '__main__':
    main()
