# Generated by Django 3.2.6 on 2021-11-03 20:01

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_userbiomention_userbiotag'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfileTagList',
            fields=[
                ('user_profile_tag_list_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('user_profile_tag_list', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=5)),
            ],
            options={
                'db_table': 'user_profile_tag_list',
                'managed': False,
            },
        ),
    ]
