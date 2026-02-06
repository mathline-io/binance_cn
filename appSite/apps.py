from django.apps import AppConfig
import sys
import appSite.globalvar as gv


class AppsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appSite'
    verbose_name = '转发管理'

    def ready(self):
        if 'test' in sys.argv:
            gv.init_global()
            return
        gv.threading_init()
