# imports
import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import itertools
import os
from matplotlib import rcParams
import glob

#from tqdm import tqdm_notebook
from tqdm.notebook import tqdm
import sys
import re
import seaborn as sns 
sns.set_style('darkgrid')

## Vorbereitung

def get_log_props(log_path, log_root_path):
    log_path = os.path.relpath(log_path, log_root_path)
    parts = log_path.split('-')
    if len(parts) > 2:
        sim = parts[0]
        ranking = parts[1]
        topic = parts[2]
        strat = parts[3]
        user = parts[4]
        crit = parts[5].split('.')[0]

        return (sim, ranking, topic, strat, user, crit)
    else:
        return 

## Relevance judgements & querynumber

# Relevance judgements
def relevance_judgements(qrels_path):
    qrels = {}
    with open(qrels_path) as f_in:
        for line in f_in.readlines():
            parts = line.split(' ')
            qrels[(parts[0],parts[2])] = parts[3]
    return qrels

# querynumber_min_max_avg(log_files): returns the minimum, maximum, and average number of queries in "log_files" (and can be used to decide how many queries should be considered for the evaluation)
def querynumber_min_max_avg(log_files):
    minq = 0
    maxq = 0
    sumq = 0
    count = 0
    for path in log_files:
        count += 1
        currentq = 0
        with open(path) as f_in:
            for line in f_in.readlines():
                parts = line.split(' ')
                if parts[1] == 'QUERY':
                    currentq += 1
        if currentq < minq or minq == 0:
            minq = currentq
        if currentq > maxq:
            maxq = currentq
        sumq += currentq
    avgq = sumq/count

    return [minq, maxq, round(avgq)]

## Allgemeine Hilfsfunktionen

# levelname (level): Gibt den Namen eines Evaluationslevels zurück (Überschrift für die Grafiken & Dateiname beim Speichern der Grafiken)
def levelname(level, levels, levelnames):
    evaluation_level = 'NO_NAME'
    for l in range (0, len(levels)):
        if level == levels[l]:
            evaluation_level = levelnames[l]
    return evaluation_level

# fixed_combinations(...): combinations that are suitable for the evaluation
# Gibt alle Kombinationen von Levelausprägungen an, die es für jede Ausprägung des Evaluationslevels gibt, mit (teilweise) festgesetzten Werten.
# So werden beispielsweise bei der Evaluation der Query-Strategie nur die User-Typen einbezogen, für die es log-Dateien mit allen möglichen Query-Strategien gibt
def fixed_combinations(fixed_list, level_index, sim, levels, log_df):
    fixed_list.remove(levels[level_index])
    combinations = [p for p in itertools.product(*fixed_list)]
    existing_l = [l for l in levels[level_index] if ((log_df['Simulation'] == sim) & (log_df.iloc[:,level_index+1] == l)).any()] # falls es Ausprägungen des zu evaluierenden Levels nicht in der betrachteten Simulation gibt
    combis = []
    for combination in combinations:
        p = True
        for lev in existing_l:
            cl = list(combination)
            cl.insert(level_index, lev)
            ranking = cl[0]
            query_type = cl[1]
            user = cl[2]
            crit = cl[3]
            if not ((log_df['Simulation'] == sim) & (log_df['Ranking'] == ranking) & (log_df['Strat'] == query_type) & (log_df['User'] == user) & (log_df['Crit'] == crit)).any():
                p = False
        if p == True:
            for lev in existing_l:
                x = list(combination)
                x.insert(level_index, lev)
                combis.append(x)
    return combis

## Plots

# figure size in inches
rcParams['figure.figsize'] = 4,4

def dfl_sdcg(level, level_eval_all, querynumber):
    df_l = {}
    for l in level:
        l_df = pd.DataFrame.from_dict(level_eval_all[l], orient="index").stack().to_frame()
        l_df = pd.DataFrame(l_df[0].values.tolist(), index=l_df.index).reset_index(names=['topic', 'query'])
        l_df = l_df.rename(columns={0: 'gain'})
        l_df = l_df[l_df.apply(lambda row: row['query'] <=querynumber, axis=1)]
        df_l[l] = l_df

    return df_l

def dfl_effeff(level, level_eval_all):
    df_l = {}

    for l in level:
        l_df = pd.DataFrame.from_dict(level_eval_all[l], orient="index").stack().to_frame()
        l_df = pd.DataFrame(l_df[0].values.tolist(), index=l_df.index).reset_index(names=['topic', 'cost'])
        l_df = l_df.rename(columns={0: 'gain'})
        l_df = l_df[l_df.apply(lambda row: row['cost'] <=10000, axis=1)]
        df_l[l] = l_df

    return df_l

def dfl_srbp(level, level_eval_all, querynumber):
    df_l = {}

    for l in level:
        l_df = pd.DataFrame.from_dict(level_eval_all[l], orient="index").stack().to_frame()
        l_df = pd.DataFrame(l_df[0].values.tolist(), index=l_df.index).reset_index(names=['topic', 'query'])
        l_df = l_df.rename(columns={0: 'gain'})
        l_df = l_df[l_df.apply(lambda row: row['query'] <=querynumber, axis=1)]
        df_l[l] = l_df

    return df_l

def lineplot_sdcg(level, evaluation_level, level_eval_all, querynumber, ax):
    
    df_l = dfl_sdcg(level, level_eval_all, querynumber)

    for l in level:
        sns.lineplot(data=df_l[l], x='query', y='gain', label=l, ax = ax)


def lineplot_effeff(level, evaluation_level, level_eval_all, ax):
    
    df_l = dfl_effeff(level, level_eval_all)

    for l in level:
        sns.lineplot(data=df_l[l], x='cost', y='gain', label=l, ax = ax)



def lineplot_srbp(level, evaluation_level, level_eval_all, querynumber, ax):
    
    df_l = dfl_srbp(level, level_eval_all, querynumber)

    for l in level:
        sns.lineplot(data=df_l[l], x='query', y='gain', label=l, ax=ax)



def histplots_sdcg(level, evaluation_level, level_eval_all, querynumber, ax):
    
    df_l = dfl_sdcg(level, level_eval_all, querynumber)

    for l in level:
        sns.histplot(df_l[l], x ='gain', label = l, legend=True, ax = ax)

    ax.legend()


def histplots_effeff(level, evaluation_level, level_eval_all, ax):
    
    df_l = dfl_effeff(level, level_eval_all)

    for l in level:
        sns.histplot(df_l[l], x ='gain', label = l, legend=True, ax=ax)

    ax.legend()


def histplots_srbp(level, evaluation_level, level_eval_all, querynumber, ax):
    
    df_l = dfl_srbp(level, level_eval_all, querynumber)

    for l in level:
        sns.histplot(df_l[l], x ='gain', label = l, legend=True, ax=ax)

    ax.legend()

## Topics to analyze

def available_topics(log_df, sim, ranking, query_type, user, crit):
    res = []
    for index, row in log_df.iterrows():
        if ((row['Simulation'] == sim) & (row['Ranking'] == ranking) & (row['Strat'] == query_type) & (row['User'] == user) & (row['Crit'] == crit)):
            res.append(row['Topics'])
    return res

def available_topics_combinations(log_df, sim, combinations):
    topic_lists = []
    for combi in combinations:
        topics_combi = available_topics(log_df, sim, combi[0], combi[1], combi[2], combi[3])
        topic_lists.append(topics_combi)
    res = [x for x in topic_lists[0] if all(x in sublist for sublist in topic_lists)]
    return res

## Files to consider

# sim_files(...): returns all files that belong to a specific simulation
def sim_files(sim, log_files):
    for l in log_files:
        simfiles = [l for l in log_files if re.split(r'-|\\|/',l.split('-')[0])[-1] == sim]
    return simfiles

def filter_logfiles(logfiles, sims = 'all', rankings = 'all', strats = 'all', users= 'all', crits = 'all', topics = 'all'):
    res = []
    log_root_path = '/'.join(re.split(r'\\|/',logfiles[0])[:-1])+'/'
    for logfile in logfiles: 
        props = get_log_props(logfile, log_root_path)
        if (sims == 'all' or props[0] in sims) and (rankings == 'all' or props[1] in rankings) and (topics == 'all' or props[2] in topics) and (strats == 'all' or props[3] in strats) and (users == 'all' or props[4] in users) and (crits == 'all' or props[5] in crits):
            res.append(logfile)
    return res

