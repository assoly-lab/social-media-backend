# Generated by Django 5.1.2 on 2024-11-01 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_commentlike'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(default='avatars/user.jpg', upload_to='avatars/'),
        ),
    ]
