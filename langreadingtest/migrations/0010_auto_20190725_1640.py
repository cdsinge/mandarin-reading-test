# Generated by Django 2.2.3 on 2019-07-25 15:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('langreadingtest', '0009_auto_20190721_1714'),
    ]

    operations = [
        migrations.RenameField(
            model_name='quiz',
            old_name='dataset',
            new_name='word_dataset',
        ),
    ]