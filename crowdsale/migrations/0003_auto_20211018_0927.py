# Generated by Django 3.2.7 on 2021-10-18 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crowdsale', '0002_investor'),
    ]

    operations = [
        migrations.CreateModel(
            name='Whitepaper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload', models.FileField(upload_to='uploads/')),
            ],
        ),
        migrations.DeleteModel(
            name='Investor',
        ),
    ]
