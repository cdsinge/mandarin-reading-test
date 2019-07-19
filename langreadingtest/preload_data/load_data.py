# Run this in the shell (from project directory)
# python manage.py shell
# There are several alternatives to this, custom command, data migration, dumpdata/loaddata

from langreadingtest.models import ChineseWord
existing = ChineseWord.objects.all()
for e in existing:
    e.delete()
import pandas

if 0:
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
else:
    csv_file = 'langreadingtest\preload_data\most_freq_utf8.txt'
    to_load = pandas.read_csv(csv_file, sep='\t', header=None,
        names=['id', 'simp', 'raw_freq', 'freq_cdf',  'pinyin', 'defn'], index_col=False)

    prev_cdf = 0
    for idx,x in to_load.iterrows():
        if (idx % 1000) == 0:
            print (idx)
        try:
            definition = x.defn[:100]
        except TypeError:
            print ('No definition for {}'.format(x.simp))
            definition = '(Uh-oh, missing definition)'
        if len(definition) > 90:
            definition = definition[:definition.rfind(';')]

        cdf = x['freq_cdf']/100.
        pdf = cdf - prev_cdf
        prev_cdf = cdf
        cw = ChineseWord(simplified=x.simp,
                         pinyin=x.pinyin,
                         definition=definition,
                         pdf=pdf)
        cw.full_clean()
        cw.save()

# This iterative approach is slow, consider alternatives
