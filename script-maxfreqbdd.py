from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.bdd import BDD
from dtcontrol.pre_processing.norm_pre_processor import NormPreProcessor
from dtcontrol.pre_processing.maxfreq_pre_processor import MaxFreqPreProcessor

suite = BenchmarkSuite(timeout=900,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark_file-maxfreqbdd',
                       rerun=False)

suite.add_datasets(['examples/storm', 'examples/cps'])

#bdd_minnorm_0 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=0)
bdd_maxfreq_0 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=10)
bdd_maxfreq_1 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=11)
bdd_maxfreq_2 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=12)
bdd_maxfreq_3 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=13)
bdd_maxfreq_4 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=14)
bdd_maxfreq_5 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=15)
bdd_maxfreq_6 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=16)
bdd_maxfreq_7 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=17)
bdd_maxfreq_8 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=18)
bdd_maxfreq_9 = BDD(1, label_pre_processor=MaxFreqPreProcessor(),name_suffix=19)

classifiers = [
#    bdd_minnorm_0,
    bdd_maxfreq_0,
    bdd_maxfreq_1,
    bdd_maxfreq_2,
    bdd_maxfreq_3,
    bdd_maxfreq_4,
    bdd_maxfreq_5,
    bdd_maxfreq_6,
    bdd_maxfreq_7,
    bdd_maxfreq_8,
    bdd_maxfreq_9,
]
suite.benchmark(classifiers)
#suite.display_html()
