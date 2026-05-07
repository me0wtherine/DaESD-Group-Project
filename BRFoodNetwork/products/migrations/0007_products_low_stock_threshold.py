from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_reviews'),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='low_stock_threshold',
            field=models.PositiveIntegerField(
                default=5,
                help_text='Producer will be alerted when stock falls below this number.',
            ),
        ),
    ]
