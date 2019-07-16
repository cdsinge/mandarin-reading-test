# Generated by Django 2.2.3 on 2019-07-16 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('langreadingtest', '0004_auto_20190713_0100'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_position', models.IntegerField()),
                ('previous_answer_correct', models.BooleanField(default=True)),
                ('step_size', models.IntegerField()),
                ('correct_list', models.CharField(max_length=300)),
                ('incorrect_list', models.CharField(max_length=300)),
            ],
        ),
    ]
