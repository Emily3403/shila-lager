# Generated by Django 5.0.4 on 2024-05-07 16:23

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
                ('id', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('content', models.CharField(max_length=64)),
                ('bottle_type',
                 models.CharField(choices=[('glass', 'Glass Bottle'), ('single_glass_bottle', 'Single Glass Bottle'), ('plastic', 'Pet Plastic'), ('tetra_pack', 'Tetra Pack'), ('package', 'Package'), ('crate_return', 'Crate Return'), ('bonus_credit', 'Bonus Credit'), ('unknown', 'Unknown')],
                                  default='glass', max_length=64)),
            ],
            options={
                'verbose_name_plural': 'Beverage Crates',
                'unique_together': {('name', 'content')},
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
        migrations.CreateModel(
            name='GrihedPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('deposit', models.DecimalField(decimal_places=2, max_digits=8)),
                ('valid_from', models.DateTimeField()),
                ('crate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grihed_price', to='bestellung.beveragecrate', verbose_name='Beverage Crate ID')),
            ],
            options={
                'verbose_name_plural': 'Grihed Prices',
                'unique_together': {('crate_id', 'valid_from')},
            },
        ),
        migrations.CreateModel(
            name='SalePrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=4)),
                ('valid_from', models.DateTimeField()),
                ('crate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sale_prices', to='bestellung.beveragecrate', verbose_name='Beverage Crate ID')),
            ],
            options={
                'verbose_name_plural': 'Sale Prices',
                'unique_together': {('crate_id', 'valid_from')},
            },
        ),
    ]
