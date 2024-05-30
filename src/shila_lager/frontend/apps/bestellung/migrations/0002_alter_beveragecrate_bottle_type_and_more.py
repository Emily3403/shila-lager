# Generated by Django 5.0.4 on 2024-05-20 13:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bestellung', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='beveragecrate',
            name='bottle_type',
            field=models.CharField(choices=[('glass', 'Glass Bottle'), ('single_glass_bottle', 'Single Glass Bottle'), ('plastic', 'Pet Plastic'), ('tetra_pack', 'Tetra Pack'), ('package', 'Package'), ('crate_return', 'Crate Return'), ('bonus_credit', 'Bonus Credit'), ('unknown', 'Unknown')],
                                   max_length=64),
        ),
        migrations.AlterField(
            model_name='grihedprice',
            name='crate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grihed_prices', to='bestellung.beveragecrate', verbose_name='Beverage Crate ID'),
        ),
    ]
