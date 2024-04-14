# Generated by Django 5.0.4 on 2024-04-18 11:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BeverageCrate',
            fields=[
                ('name', models.CharField(max_length=256, unique=True)),
                ('grihed_id', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('number_of_bottles', models.IntegerField(default=20)),
                ('ml_in_each_bottle', models.IntegerField(default=500)),
                ('price', models.DecimalField(decimal_places=2, max_digits=4)),
                ('deposit', models.DecimalField(decimal_places=2, default=4.5, max_digits=4)),
                ('selling_price_per_bottle', models.DecimalField(decimal_places=2, max_digits=4)),
                ('bottle_type', models.CharField(choices=[('glass', 'Glass'), ('plastic', 'Plastic')], default='glass', max_length=64)),
            ],
            options={
                'verbose_name_plural': 'Beverage Crates',
            },
        ),
        migrations.CreateModel(
            name='CrateInventory',
            fields=[
                ('crate', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='inventory', serialize=False, to='bestellung.beveragecrate', verbose_name='Beverage Crate')),
                ('current_stock', models.IntegerField()),
                ('should_be_in_stock', models.IntegerField()),
            ],
            options={
                'verbose_name_plural': 'Crate Inventories',
            },
        ),
    ]
