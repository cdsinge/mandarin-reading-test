# Generated by Django 2.2.3 on 2019-07-12 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('langreadingtest', '0002_auto_20190711_1842'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chineseword',
            name='pinyin',
            field=models.CharField(max_length=30),
        ),
    ]