# Generated by Django 2.2.3 on 2019-07-11 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChineseWord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('simplified', models.CharField(max_length=10)),
                ('pinyins', models.CharField(max_length=20)),
                ('definition', models.CharField(max_length=100)),
            ],
        ),
    ]
