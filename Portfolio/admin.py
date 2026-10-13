from django.contrib import admin

from .models import Portfolio, PortfolioURL, PortfolioView, Resume


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "template_choice", "view_count", "unique_visitor_count", "last_viewed_at")
    search_fields = ("user__username", "name")
    readonly_fields = ("view_count", "unique_visitor_count", "last_viewed_at")


@admin.register(PortfolioView)
class PortfolioViewAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "device_type", "referer", "created_at")
    list_filter = ("device_type", "created_at")
    search_fields = ("portfolio__user__username", "referer")


admin.site.register(Resume)
admin.site.register(PortfolioURL)
