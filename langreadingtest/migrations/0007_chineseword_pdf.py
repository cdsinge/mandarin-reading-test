# Generated by Django 2.2.3 on 2019-07-17 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('langreadingtest', '0006_quiz_finished'),
    ]

    operations = [
        migrations.AddField(
            model_name='chineseword',
            name='pdf',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
