# Generated by Django 2.0.2 on 2020-07-21 10:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CommonExchange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_unit', models.PositiveIntegerField(default=100)),
                ('f_buy_price', models.FloatField()),
                ('m_buy_price', models.FloatField()),
                ('f_sell_price', models.FloatField()),
                ('m_sell_price', models.FloatField()),
                ('bank_conversion_price', models.FloatField()),
                ('is_common', models.BooleanField()),
                ('created', models.DateTimeField(blank=True, editable=False, null=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('sequence', models.IntegerField(default=0)),
                ('created', models.DateTimeField(blank=True, editable=False, null=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['sequence'],
            },
        ),
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchagne', models.FloatField()),
                ('result', models.FloatField()),
                ('update_time', models.CharField(max_length=30)),
                ('created', models.DateTimeField(blank=True, editable=False, null=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('from_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_currency', to='tools.Currency')),
                ('to_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_currency', to='tools.Currency')),
            ],
        ),
        migrations.AddField(
            model_name='commonexchange',
            name='from_currency',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='common_from_currency', to='tools.Currency'),
        ),
        migrations.AddField(
            model_name='commonexchange',
            name='to_currency',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='common_to_currency', to='tools.Currency'),
        ),
    ]
