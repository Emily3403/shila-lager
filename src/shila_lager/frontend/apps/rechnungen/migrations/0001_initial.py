# Generated by Django 5.0.6 on 2024-05-09 13:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('bestellung', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GrihedInvoice',
            fields=[
                ('invoice_number', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('date', models.DateTimeField()),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=16)),
            ],
            options={
                'verbose_name_plural': 'Grihed Invoices',
            },
        ),
        migrations.CreateModel(
            name='ShilaAccountBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('booking_date', models.DateField()),
                ('value_date', models.DateField()),
                ('kind', models.CharField(choices=[('Lastschrift', 'Lastschrift'), ('LS Wiedergutschrift', 'Lastschrift Undo'), ('Dauerauftrag', 'Dauerauftrag'), ('Rechnung', 'Rechnung'), ('Kartenzahlung', 'Kartenzahlung'), ('Online-Uberweisung', 'Onlineuberweisung'), ('Gutschrift', 'Gutschrift'),
                                                   ('Bargeldeinzahlung', 'Bargeldeinzahlung'), ('Abschluss', 'Abschluss'), ('Entgeldabschluss', 'Entgeltabschluss')], max_length=64)),
                ('description', models.CharField(max_length=256)),
                ('creditor_id', models.CharField(max_length=64, null=True)),
                ('mandate_reference', models.CharField(max_length=64, null=True)),
                ('customer_reference', models.CharField(max_length=64, null=True)),
                ('collector_reference', models.CharField(max_length=64, null=True)),
                ('original_amount', models.DecimalField(decimal_places=2, max_digits=16, null=True)),
                ('chargeback_amount', models.DecimalField(decimal_places=2, max_digits=16, null=True)),
                ('beneficiary_or_payer', models.CharField(
                    choices=[('GRIHED Service GmbH', 'Grihed'), ('Team Getränke', 'Team Getränke'), ('GEPA MBH', 'Gepa'), ('DM-drogerie markt', 'Dm'), ('Hetzner Online GmbH', 'Hetzner'), ('Berliner Sparkasse', 'Sparkasse'), ('TU Berlin', 'Tu Berlin'), ('VPSL', 'Vpsl'), ('Emily Seebeck', 'Emily'),
                             ('Leander Guelland', 'Lelle'), ('Ilja Behnke', 'Ille'), ('Jonas Pasche', 'Jonas'), ('Jette Eckel', 'Jette'), ('Helge Kling', 'Helge'), ('Fabian Ruben', 'Fabian'), ('Elias Tretin', 'Elias'), ('Andere Personen', 'Andere Personen'), ('Sonstiges', 'Sonstiges')],
                    max_length=64, null=True)),
                ('iban', models.CharField(max_length=64)),
                ('bic', models.CharField(max_length=64)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=16)),
                ('currency', models.CharField(max_length=16)),
                ('additional_info', models.CharField(max_length=256)),
            ],
            options={
                'verbose_name_plural': 'Shila Account Bookings',
            },
        ),
        migrations.CreateModel(
            name='GrihedInvoiceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('name', models.CharField(max_length=256)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=16)),
                ('beverage', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='invoice_items', to='bestellung.beveragecrate')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='items', to='rechnungen.grihedinvoice')),
                ('purchase_price', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='invoice_items', to='bestellung.grihedprice')),
                ('sale_price', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='invoice_items', to='bestellung.saleprice')),
            ],
            options={
                'verbose_name_plural': 'Grihed Invoice Items',
                'unique_together': {('invoice', 'beverage')},
            },
        ),
    ]
