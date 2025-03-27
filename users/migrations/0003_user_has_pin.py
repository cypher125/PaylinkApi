from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_account_status_user_occupation'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='has_pin',
            field=models.BooleanField(default=False),
        ),
    ]
