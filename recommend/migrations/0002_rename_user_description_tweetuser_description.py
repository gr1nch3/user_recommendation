# Generated by Django 5.0.7 on 2024-07-20 16:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recommend', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tweetuser',
            old_name='user_description',
            new_name='description',
        ),
    ]
