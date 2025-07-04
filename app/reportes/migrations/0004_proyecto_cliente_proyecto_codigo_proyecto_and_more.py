# Generated by Django 4.2.10 on 2025-05-19 22:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0003_proyecto_alter_reportefotografico_proyecto'),
    ]

    operations = [
        migrations.AddField(
            model_name='proyecto',
            name='cliente',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Cliente'),
        ),
        migrations.AddField(
            model_name='proyecto',
            name='codigo_proyecto',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Código del proyecto'),
        ),
        migrations.AddField(
            model_name='proyecto',
            name='contratista',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Contratista'),
        ),
        migrations.AddField(
            model_name='proyecto',
            name='inicio_supervision',
            field=models.DateField(blank=True, null=True, verbose_name='Inicio de Supervisión'),
        ),
    ]
