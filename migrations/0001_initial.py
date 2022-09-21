# Generated by Django 3.2.6 on 2021-08-10 22:50

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=20)),
                ('email', models.EmailField(max_length=254)),
                ('password', models.CharField(max_length=25, validators=[django.core.validators.MinLengthValidator(8)])),
                ('display_picture', models.CharField(max_length=200)),
                ('is_verified', models.BooleanField(default=False)),
                ('joined_at', models.DateTimeField(default=datetime.datetime.now)),
            ],
        ),
        migrations.CreateModel(
            name='venues',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, max_length=500)),
                ('price', models.IntegerField()),
                ('booking_link', models.TextField()),
                ('location_lat', models.DecimalField(decimal_places=6, max_digits=9)),
                ('location_long', models.DecimalField(decimal_places=6, max_digits=9)),
            ],
        ),
        migrations.CreateModel(
            name='post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(default=datetime.datetime.now)),
                ('media', models.CharField(max_length=200)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.users')),
                ('venue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.venues')),
            ],
        ),
    ]
