# Run this in the shell (from project directory)
# python manage.py shell
# There are several alternatives to this, custom command, data migration, dumpdata/loaddata

from langreadingtest.models import ChineseWord
existing = ChineseWord.objects.all()
for e in existing:
    e.delete()
import pandas
#to_load = pandas.read_csv('preload_data\HSK Official With Definitions 2012 L6 freqorder.txt')
csv_file = 'langreadingtest\preload_data\HSK Official With Definitions 2012 L6 freqorder.txt'
to_load = pandas.read_csv(csv_file, sep='\t', header=None,
    names=['simp', 'trad', 'pinyin_no_mark', 'pinyin', 'defn'], index_col=False)

for _,x in to_load.iterrows():
    definition = x.defn[:100]
    if len(definition) > 90:
        definition = definition[:definition.rfind(';')]
    cw = ChineseWord(simplified=x.simp,
                     pinyin=x.pinyin,
                     definition=definition)
    cw.full_clean()
    cw.save()
