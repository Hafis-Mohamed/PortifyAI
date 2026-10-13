from django.db import migrations, models
from django.db.models import Count, Max


def backfill_counters(apps, schema_editor):
    Portfolio = apps.get_model('Portfolio', 'Portfolio')
    PortfolioView = apps.get_model('Portfolio', 'PortfolioView')
    stats = (
        PortfolioView.objects.values('portfolio_id')
        .annotate(views=Count('id'), uniques=Count('visitor_hash', distinct=True), last=Max('created_at'))
    )
    for row in stats:
        Portfolio.objects.filter(pk=row['portfolio_id']).update(
            view_count=row['views'],
            unique_visitor_count=row['uniques'],
            last_viewed_at=row['last'],
        )


class Migration(migrations.Migration):

    dependencies = [
        ('Portfolio', '0005_portfolioview'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolio',
            name='view_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='unique_visitor_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='last_viewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_counters, migrations.RunPython.noop),
    ]
