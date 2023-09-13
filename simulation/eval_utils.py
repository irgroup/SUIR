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
def fixed_combinations(fixed_list, level_index, sim, levels, log_root_path, topics_to_analyze, log_df):
    fixed_list.remove(levels[level_index])
    combinations = [p for p in itertools.product(*fixed_list)]
    existing_l = [l for l in levels[level_index] if ((log_df['Simulation'] == sim) & (log_df.iloc[:,level_index+1] == l)).any()] # falls es Ausprägungen des zu evaluierenden Levels nicht in der betrachteten Simulation gibt
    print(existing_l)
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
            if not os.path.isfile(log_root_path + sim + "-" + ranking + "-" + str(next(iter(topics_to_analyze))) + "-" + query_type + "-" + user + "-" + crit + ".log"):
                p = False
        if p == True:
            for lev in existing_l:
                x = list(combination)
                x.insert(level_index, lev)
                combis.append(x)
    return combis
# Es wird vorausgesetzt, dass es die logs zu allen Themen gibt (Überprüfung nur für das erste Thema)

# sim_files(...): returns all files that belong to a specific simulation
def sim_files(sim, log_files):
    for l in log_files:
        simfiles = [l for l in log_files if re.split(r'-|\\|/',l.split('-')[0])[-1] == sim]
    return simfiles

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

def dfl_effeff(level, level_eval_all, querynumber):
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


def lineplot_effeff(level, evaluation_level, level_eval_all, querynumber, ax):
    
    df_l = dfl_effeff(level, level_eval_all, querynumber)

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


def histplots_effeff(level, evaluation_level, level_eval_all, querynumber, ax):
    
    df_l = dfl_effeff(level, level_eval_all, querynumber)

    for l in level:
        sns.histplot(df_l[l], x ='gain', label = l, legend=True, ax=ax)

    ax.legend()


def histplots_srbp(level, evaluation_level, level_eval_all, querynumber, ax):
    
    df_l = dfl_srbp(level, level_eval_all, querynumber)

    for l in level:
        sns.histplot(df_l[l], x ='gain', label = l, legend=True, ax=ax)

    ax.legend()

