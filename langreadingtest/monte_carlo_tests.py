"""
TODO don't use the main database

Goal, to test the approach used.
To test:
    for all datasets (or datasets of all sizes, can even invent the datasets just for testing)
      (say, a dataset of 100 words, a dataset of 1000 words and one of 20000 words)
    given a totally known set of words, that honestly answers, check given estimate is close to reality, and create some confidence interval.
    That an appropriate number of steps are used (and no bad cases of too few/many steps)

This is a test of approach, don't need to reuse existing code/db if simple enough, but is better to use same code
"""
from django.test import TestCase
from .models import Quiz,ChineseWord,WordDataset
from . import views,models
import pandas as pd
import numpy as np
import logging
import random
from sklearn.isotonic import IsotonicRegression

logging.basicConfig(level=logging.INFO)

class FakeUser(object):
    def __init__(self, ):
        super().__init__()
        self.known_word_ids = []

    def add_word(self, new_word_id):
        self.known_word_ids.append(new_word_id)

    def is_word_known(self, word_id):
        return word_id in self.known_word_ids


# TODO would be nice to do this outside of the unittest framework too.
class MonteCarloTest(TestCase):
    def setUp(self):
        # ds = WordDataset()
        # ds.save()
        WordDataset.objects.create(name='100words')
        WordDataset.objects.create(name='1000words')
        WordDataset.objects.create(name='10000words')
        # exact dataset used doesn't matter, just use any that has a frequency count
        #most_freq_df = pandas.read_csv(r'preload_data/most_freq_utf8.txt', delimiter='\t', header=None, index_col=0, names=['Simplified','total_count','cumul_freq','pinyin','defn'])
        csv_file = 'langreadingtest\preload_data\most_freq_utf8.txt'
        to_load = pd.read_csv(csv_file, sep='\t', header=None,
            names=['id', 'Simplified', 'raw_freq', 'freq_cdf',  'pinyin', 'defn'], index_col=False)

        for (n, word_ds_name) in ((100,'100words'), (1000, '1000words'), (10000, '10000words')):
            word_ds = WordDataset.objects.get(name=word_ds_name)
            load_sliced = to_load[0:n].copy()
            freq_sum = load_sliced['raw_freq'].sum()
            load_sliced['rel_freq'] = load_sliced['raw_freq']/freq_sum
            for _,r in load_sliced.iterrows():
                defn = r['defn']
                if type(defn) != str and np.isnan(defn):
                    defn = 'Oops, missing'
                defn = defn[:100]
                cw = ChineseWord(simplified=r['Simplified'], definition=defn, pinyin=r['pinyin'],
                                normalised_freq=r['rel_freq'], dataset=word_ds)
                cw.full_clean()
                cw.save()

        #df = pd.read_excel(r'preload_data//HSK-2012.xls', header=None, names=['Simplified'])

        # q.save()

        # create_chinese_word_objects(150)
        # current_position = 20
        # step_size = 10
        # Quiz.objects.create(id=1,
        #                     current_position=current_position,
        #                     step_size=step_size)

    # def create_dataset(n):
    #     return list(range(0,n))  # 0 .. n-1

    def create_fake_user(self, num_known_words, word_ds):
        # Create a fake user with knowing num_known_words proportional to their frequencies
        fake_user = FakeUser()

        all_words = []
        for w in word_ds.chineseword_set.all():
            all_words.append((w.normalised_freq,w.id))
        probs,ids = zip(*all_words)

        # Would be fun to understand np.random.choice at https://github.com/numpy/numpy/blob/master/numpy/random/mtrand.pyx
        known_word_ids = np.random.choice(ids, size=num_known_words, replace=False, p=probs)
        for kw_id in known_word_ids:
            fake_user.add_word(kw_id)
        logging.debug(f'Created user knowing {num_known_words} words')
        return fake_user

    def test_word_datasets(self):
        # have users knowing 0, 10, 20,  ... 100 words, x repetitions of each
        # first sample the words...  the simplest case linear generation
        for (word_ds_name, dataset_size, known_words_step_increase) in [
                        ('100words', 100, 10),
                        ('1000words', 1000, 100)]:
            word_dataset = WordDataset.objects.get(name=word_ds_name)
            repeat = 1#5
            known_words = 0
            while known_words <= dataset_size:
                for _ in range(repeat):
                    fake_user = self.create_fake_user(known_words, word_dataset)

                    q = models.create_quiz(word_dataset)
                    # test_size = word_dataset.chineseword_set.all().count()
                    # random_int = random.randint(-5,5)
                    # initial_position = round(test_size*0.2) + random_int
                    # initial_step_size = round(min(10,test_size*0.04))
                    # q = Quiz(word_dataset=word_dataset, current_position=initial_position, step_size=initial_step_size)
                    quiz_id = q.id
                    while not q.finished:
                        word_id = q.get_word_id_at_current_position()
                        q.update_next_word(word_id, fake_user.is_word_known(word_id))
                    logging.info(f'ID: {q.id}. Step count: {q.get_number_answered()}. Known: {known_words}. Estimate {q.get_number_words()} '\
                                 f'Pos {q.current_position}')

                    # plot graphs as it's not working...
                    # better to just output the data, and plot outside of runtime
                    import matplotlib.pyplot as plt
                    plt.figure()
                    plt.plot(q.get_correct_list_as_ints(), [1]*len(q.get_correct_list_as_ints()), 'o')
                    plt.plot(q.get_incorrect_list_as_ints(), [0]*len(q.get_incorrect_list_as_ints()), 'o')
                    # plt.plot(q.get_seen_list(), )

                    xs = [-50]+q.get_correct_list_as_ints() + q.get_incorrect_list_as_ints()+[q.get_test_size()+50]
                    ys = ([1]*(1+len(q.get_correct_list_as_ints()))) + \
                         ([0]*(1+len(q.get_incorrect_list_as_ints())))
                    # Get in position order
                    zipped_sorted = sorted(list(zip(xs,ys)), key = lambda x: x[0])
                    (xs,ys) = zip(*zipped_sorted)
                    ir = IsotonicRegression(y_max=1, y_min=0, increasing=False).fit(xs, ys)

                    xs = np.arange(0, q.get_test_size())
                    ys = ir.predict(xs)
                    plt.plot(xs,ys)
                    import os
                    plot_dir = 'plots'
                    if not os.path.exists(plot_dir):
                        os.mkdir(plot_dir)
                        ls = os.listdir(plot_dir)
                        i = 1
                        while i in ls:
                            i += 1
                        plot_dir = os.path.join(plot_dir, str(i))
                        os.mkdir(plot_dir)
                    filename = f'{plot_dir}/{q.id}_{known_words}_{q.get_number_words()}.png'
                    plt.savefig(filename)
                    plt.close()

                known_words += known_words_step_increase
