# Generated by Django 5.1.2 on 2025-06-05 17:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Geofence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('raio', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='UserGeofence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geofence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service.geofence')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'geofence')},
            },
        ),
    ]
