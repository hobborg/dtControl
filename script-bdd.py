from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.bdd import BDD
from dtcontrol.pre_processing.norm_pre_processor import NormPreProcessor
from dtcontrol.pre_processing.maxfreq_pre_processor import MaxFreqPreProcessor

suite = BenchmarkSuite(timeout=900,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark_file-BDD',
                       rerun=False)

suite.add_datasets(['examples/storm', 'examples/cps'])

bdd_actOR_0 = BDD(0,name_suffix=0)
bdd_actOR_1 = BDD(0,name_suffix=1)
bdd_actOR_2 = BDD(0,name_suffix=2)
bdd_actOR_3 = BDD(0,name_suffix=3)
bdd_actOR_4 = BDD(0,name_suffix=4)
bdd_actOR_5 = BDD(0,name_suffix=5)
bdd_actOR_6 = BDD(0,name_suffix=6)
bdd_actOR_7 = BDD(0,name_suffix=7)
bdd_actOR_8 = BDD(0,name_suffix=8)
bdd_actOR_9 = BDD(0,name_suffix=9)

bdd_actUL_0 = BDD(1,name_suffix=0)
bdd_actUL_1 = BDD(1,name_suffix=1)
bdd_actUL_2 = BDD(1,name_suffix=2)
bdd_actUL_3 = BDD(1,name_suffix=3)
bdd_actUL_4 = BDD(1,name_suffix=4)
bdd_actUL_5 = BDD(1,name_suffix=5)
bdd_actUL_6 = BDD(1,name_suffix=6)
bdd_actUL_7 = BDD(1,name_suffix=7)
bdd_actUL_8 = BDD(1,name_suffix=8)
bdd_actUL_9 = BDD(1,name_suffix=9)

#When determinizing, actor or UL makes no difference as there is only 1 action
bdd_minnorm_0 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=0)
bdd_minnorm_1 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=1)
bdd_minnorm_2 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=2)
bdd_minnorm_3 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=3)
bdd_minnorm_4 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=4)
bdd_minnorm_5 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=5)
bdd_minnorm_6 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=6)
bdd_minnorm_7 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=7)
bdd_minnorm_8 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=8)
bdd_minnorm_9 = BDD(0, label_pre_processor=NormPreProcessor(min),name_suffix=9)
bdd_maxfreq_0 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=10)
bdd_maxfreq_1 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=11)
bdd_maxfreq_2 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=12)
bdd_maxfreq_3 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=13)
bdd_maxfreq_4 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=14)
bdd_maxfreq_5 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=15)
bdd_maxfreq_6 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=16)
bdd_maxfreq_7 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=17)
bdd_maxfreq_8 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=18)
bdd_maxfreq_9 = BDD(0, label_pre_processor=MaxFreqPreProcessor(),name_suffix=19)

classifiers = [
    bdd_actOR_0,
    bdd_actOR_1,
    bdd_actOR_2,
    bdd_actOR_3,
    bdd_actOR_4,
    bdd_actOR_5,
    bdd_actOR_6,
    bdd_actOR_7,
    bdd_actOR_8,
    bdd_actOR_9,
    bdd_actUL_0,
    bdd_actUL_1,
    bdd_actUL_2,
    bdd_actUL_3,
    bdd_actUL_4,
    bdd_actUL_5,
    bdd_actUL_6,
    bdd_actUL_7,
    bdd_actUL_8,
    bdd_actUL_9,
    bdd_minnorm_0,
    bdd_minnorm_1,
    bdd_minnorm_2,
    bdd_minnorm_3,
    bdd_minnorm_4,
    bdd_minnorm_5,
    bdd_minnorm_6,
    bdd_minnorm_7,
    bdd_minnorm_8,
    bdd_minnorm_9,
#    bdd_maxfreq_0,
#    bdd_maxfreq_1,
#    bdd_maxfreq_2,
#    bdd_maxfreq_3,
#    bdd_maxfreq_4,
#    bdd_maxfreq_5,
#    bdd_maxfreq_6,
#    bdd_maxfreq_7,
#    bdd_maxfreq_8,
#    bdd_maxfreq_9,
]
suite.benchmark(classifiers)
#suite.display_html()
