from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('assets', '0011_attribution_type_and_optional_return_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attribution',
            name='client',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='attributions',
                to='assets.client',
            ),
        ),
    ]