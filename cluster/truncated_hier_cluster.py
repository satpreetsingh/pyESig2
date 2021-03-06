__author__ = 'wangnxr'

from util.error import varError
from sklearn.cluster import KMeans, AffinityPropagation
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances
from sklearn.neighbors import kneighbors_graph
import matplotlib.pyplot as plt
import cPickle as pickle
import numpy as np
from scipy.stats import mode
import time
import sys
import os

import pdb


def find_data_ind(date, index):
    for d in xrange(index.shape[0]):
        name = index[d].split('/')[-1]
        vid, rest = name.split('_')
        num, _ = rest.split('.')
        if int(vid == str(date)):
            return d


def split_cluster(cluster_data, n_clusters):
    estimator = KMeans(n_clusters, n_init=10, max_iter=500)
    estimator.fit(cluster_data)

    return estimator.labels_


def temporal_consistency(ind):
    return np.std(ind)


def hier_cluster(data, ind, prev_stdev, result, level):
    consistency = temporal_consistency(ind)

    #print "Processing level " + str(level)
    if not (data.shape[0] < 100  or level > 9):
        labels = split_cluster(data, 20/(level+1))
        most_label = mode(labels)[0][0]
        cluster0 = data[np.where(labels == most_label)[0],:]
        cluster0_ind = ind[np.where(labels == most_label)[0]]
        cluster1 = data[np.hstack([np.where(labels < most_label)[0], np.where(labels > most_label)[0]]),:]
        cluster1_ind = ind[np.hstack([np.where(labels < most_label)[0],np.where(labels > most_label)[0]])]

        result[level, cluster0_ind] = 0
        result[level, cluster1_ind] = 1
        hier_cluster(cluster0, cluster0_ind, consistency, result, level + 1)
        hier_cluster(cluster1, cluster1_ind, consistency, result, level + 1)


def add_hier(cluster_result, cluster_result_temp, level):
    # Change cluster code using binary conversion at each level
    cluster_result[level,:] = (2 ** (level)) * cluster_result_temp[level, :] + cluster_result[level-1,:]


def condense_time(cluster_result, level, rate):
    n_clusters = 2 ** (level +1)
    n_mins = int(round(cluster_result.shape[0]/(rate/2.0)))
    n_labels = np.zeros(shape=(n_mins, n_clusters))
    for h in xrange(n_mins):
        for n in xrange(n_clusters):
            n_labels[h, n] = np.where(cluster_result[h * rate / 2:(h + 1) * rate / 2.0] == n)[0].shape[0]

    return n_labels

def extract_file_num(index):
        file_nums = np.zeros(index.shape[0])
        for i, file in enumerate(index):
            name = file.split('/')[-1]
            vid, rest = name.split('_')
            num, _ = rest.split('.')
            file_nums[i] = int(num)
        return file_nums
def hier_cluster_main(sbj_id, dates, features_loc, save_loc, type = "normal"):
    if not os.path.isdir(save_loc + "\\" + sbj_id):
        os.makedirs(save_loc + "\\" + sbj_id)
    for date in dates:
        if not os.path.isfile(save_loc + "/" + sbj_id + "_" + str(date) + "_3_centers.p"):
        #if 1:
            print "Processing date: " + str(date)
            if type == "high_freq":
                index = extract_file_num(pickle.load(open(features_loc + "index_pca_" + sbj_id + "_" + str(date) + "_all_f.p", "rb")))
                data_raw = pickle.load(open(features_loc + "transformed_pca_" + sbj_id + "_" + str(date) + "_all_f.p", "rb"))[:,:50]
            else:
                index = extract_file_num(pickle.load(open(features_loc + "index_pca_" + sbj_id + "_" + str(date) + ".p", "rb")))
                data_raw = pickle.load(open(features_loc + "transformed_pca_" + sbj_id + "_" + str(date) + ".p", "rb"))[:,:50]
            order = np.argsort(index)
            data = np.zeros(shape=data_raw.shape)
            for d in xrange(data.shape[0]):
                data[d] = data_raw[order[d]]

            valid = []
            for d, datum in enumerate(data):
                if not(np.isnan(datum).any()):
                    valid.append(d)
            valid_data = data[valid,:]

            cluster_result_temp = np.zeros(shape=(10, len(valid))) - 1
            hier_cluster(valid_data, np.array(range(valid_data.shape[0])), float("inf"), cluster_result_temp, 0)
            cluster_result_temp2 = np.zeros(shape=(10,len(data)))-1
            cluster_result_temp2[:,valid] = cluster_result_temp
            cluster_result = np.zeros(shape=(10, data.shape[0]))

            cluster_result[0, :] = cluster_result_temp2[0,:]
            for level in range(1, cluster_result_temp2.shape[0]):
                add_hier(cluster_result, cluster_result_temp2, level)
                cluster_result[level,np.where(cluster_result_temp2[level,:] == -1)[0]] = -1
            for level in range(0, cluster_result_temp2.shape[0]):
                cluster_centers=[]

                for c in xrange(int(np.nanmax(cluster_result[level,:] )) + 1):

                    cluster_index = np.where(cluster_result[level,:]==c)[0]
                    if len(cluster_index>0):
                        cluster_center = np.mean(data[cluster_index], axis=0)
                        cluster_centers.append(cluster_center)
                    else:
                        cluster_centers.append([])
                pickle.dump(cluster_centers, open(save_loc + "\\" + sbj_id + "_" +
                                                  str(date) + "_" + str(level) + "_centers.p", "wb"))



            # Plot Cluster Figures
            plt.figure(figsize=(20,10))
            for l in xrange(5):
                condensed = condense_time(cluster_result[l, :], l, 16)
                index = np.argsort(condensed[:,:].sum(axis=0))

                # for c in index[-min(2**(l+1),5):]:
                #      plt.plot(np.arange(0,condensed.shape[0]*10,10),condensed[:,c])
                #
                # plt.xlabel("Time(Minute)")
                # plt.ylabel("Cluster Count")
                # #plt.xticks(np.arange(0,condensed.shape[0]*10,10))
                # plt.show()
                pickle.dump(condensed, open(save_loc + "\\" + sbj_id + "_" + str(date) + "_" + str(l) + ".p", "wb"))
            pickle.dump(cluster_result, open(save_loc + "\\" + sbj_id + "_" + str(date) + ".p", "wb"))


if __name__ == "__main__":
    if not (len(sys.argv) == 5):
        raise varError("Arguments should be <Subject ID> <Dates> <Features directory>\
                          <Save directory>")
    sys.argv[2] = sys.argv[2].split()
    hier_cluster_main(*sys.argv[1:])
