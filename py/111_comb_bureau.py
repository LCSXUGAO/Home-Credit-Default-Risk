#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 30 20:27:28 2018

@author: kazuki.onodera
"""
import pandas as pd
import numpy as np
import gc
from glob import glob
from multiprocessing import Pool
from tqdm import tqdm
from itertools import combinations
import os
import utils
utils.start(__file__)
#==============================================================================
KEY = 'SK_ID_CURR'
PREF = 'bureau'


col_num = ['DAYS_CREDIT', 'CREDIT_DAY_OVERDUE', 'DAYS_CREDIT_ENDDATE',
           'DAYS_ENDDATE_FACT', 'AMT_CREDIT_MAX_OVERDUE', 'CNT_CREDIT_PROLONG',
           'AMT_CREDIT_SUM', 'AMT_CREDIT_SUM_DEBT', 'AMT_CREDIT_SUM_LIMIT',
           'AMT_CREDIT_SUM_OVERDUE', 'DAYS_CREDIT_UPDATE', 'AMT_ANNUITY']

col_cat = ['CREDIT_ACTIVE', 'CREDIT_CURRENCY', 'CREDIT_TYPE']

col_cat_comb = list(combinations(col_cat, 2))

NTHREAD = len(col_cat_comb)

# =============================================================================
# pivot
# =============================================================================
base = utils.read_pickles('../data/bureau')
train = utils.load_train([KEY])
test = utils.load_test([KEY])

col_cat = []
for cc in col_cat_comb:
    c1, c2 = cc
    base[f'{c1}-{c2}'] = base[c1]+'-'+base[c2]
    col_cat.append(f'{c1}-{c2}')

def pivot(cat):
    li = []
    pt = pd.pivot_table(base, index=KEY, columns=cat, values=col_num)
    pt.columns = [f'{PREF}_{c[0]}-{c[1]}_mean' for c in pt.columns]
    li.append(pt)
    pt = pd.pivot_table(base, index=KEY, columns=cat, values=col_num, aggfunc=np.sum)
    pt.columns = [f'{PREF}_{c[0]}-{c[1]}_sum' for c in pt.columns]
    li.append(pt)
    pt = pd.pivot_table(base, index=KEY, columns=cat, values=col_num, aggfunc=np.std, fill_value=-1)
    pt.columns = [f'{PREF}_{c[0]}-{c[1]}_std' for c in pt.columns]
    li.append(pt)
    feat = pd.concat(li, axis=1).reset_index()
    feat.reset_index(inplace=True)
    del li, pt
    gc.collect()
    
    df = pd.merge(train, feat, on=KEY, how='left').drop(KEY, axis=1)
    utils.to_pickles(df, f'../data/tmp_111_{cat}_train', utils.SPLIT_SIZE)
    gc.collect()
    
    df = pd.merge(test, feat, on=KEY, how='left').drop(KEY, axis=1)
    utils.to_pickles(df,  f'../data/tmp_111_{cat}_test',  utils.SPLIT_SIZE)
    gc.collect()

    
# =============================================================================
# 
# =============================================================================
pool = Pool(NTHREAD)
callback = pool.map(pivot, col_cat)
pool.close()


# =============================================================================
# concat
# =============================================================================


train = pd.concat([utils.read_pickles(f) for f in sorted(glob(f'../data/tmp_111_*_train'))], axis=1)
utils.to_pickles(train, '../data/111_train', utils.SPLIT_SIZE)


test = pd.concat([utils.read_pickles(f) for f in sorted(glob(f'../data/tmp_111_*_test'))], axis=1)
utils.to_pickles(test,  '../data/111_test',  utils.SPLIT_SIZE)


os.system('rm -rf ../data/tmp_111*')


#==============================================================================
utils.end(__file__)



