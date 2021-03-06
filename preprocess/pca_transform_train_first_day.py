import numpy as np
from glob import glob
import sys
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pdb
import cPickle as pickle
from sklearn.decomposition import PCA

def load_and_track(f, file, total):
    if f%100==0:
        print "loading file " + str(f) + " of " + str(total) + " for file " + file
    data = pickle.load(open(file,"rb"))[:,:35]

    data[np.where(data>10**11)] = np.nan

    return data

sbj_id_all = ["d6532718", "cb46fd46", "fcb01f7a", "a86a4375", "c95c1e82", "e70923c4" ]
dates_all = [[4,5,6,7], [7,8,9,10], [8,10,11,12], [4,5,6,7], [4,5,6,7], [4,5,6,7]]
components = 50

#sbj_id = "ffb52f92"
#days = [3,4,5,6,7]
for s, sbj_id in enumerate(sbj_id_all):
    train_day = dates_all[s][0]
    days = dates_all[s][1:]
    pca = pickle.load(open("D:\\ecog_processed\\d_reduced\\transformed_pca_model_" + sbj_id + "_" + str(train_day) + ".p", "rb"))
    for day in days:
        #datapath = "/media/nancy/Picon/ecog_processed/" + sbj_id + "/" + str(day) + "_"
        datapath = "D:\\ecog_processed\\" + sbj_id + "\\" + str(day) + "_"
        files_eeg = glob(datapath + '*.p')
        assert len(files_eeg) > 0, "Unable to read files!"
        new_files_eeg = []
        for f in files_eeg:
            name = f.split('\\')[-1]
            vid, rest = name.split('_')
            num, _ = rest.split('.')
            if int(vid)==day:
                new_files_eeg.append(f)

        files_eeg = np.array(new_files_eeg)
        total_files = len(files_eeg)

        #pickle.dump(files_eeg, open("/media/nancy/Picon/ecog_processed/d_reduced/index_pca_" + sbj_id + "_" + str(day) + ".p", "wb"))
        pickle.dump(files_eeg, open("D:\\ecog_processed\\d_reduced\\index_pca_" + sbj_id + "_" + str(day) + "_train_first_day.p", "wb"))

        X_eeg = np.array([load_and_track(f, file, total_files)
                          for (f, file) in enumerate(files_eeg)], dtype= 'float64')


        X_eeg -= np.nanmean(X_eeg, axis=0)

        X_eeg /= np.nanstd(X_eeg, axis=0)

        X_eeg_no_nan_l=[]
        valid_pos = []
        for i,x in enumerate(X_eeg):
            if not np.isnan(x).any():
                X_eeg_no_nan_l.append(np.ndarray.flatten(x))
                valid_pos.append(i)
        print len(valid_pos)/float(len(X_eeg))
        X_eeg_no_nan = np.array(X_eeg_no_nan_l)
        result = np.empty(shape=(X_eeg.shape[0], components))
        result[:,:] = np.nan
        result_temp = pca.transform(X_eeg_no_nan)
        result[valid_pos,:] = result_temp

        pickle.dump(result, open("/media/nancy/Picon/ecog_processed/d_reduced/transformed_pca_" + sbj_id + "_" + str(day) + "_train_first_day.p", "wb"))
        pickle.dump(valid_pos, open("/media/nancy/Picon/ecog_processed/d_reduced/valid_pos_" + sbj_id + "_" + str(day) + "_train_first_day.p", "wb"))
        #pickle.dump(result, open("D:\\ecog_processed\\d_reduced\\transformed_pca_" + sbj_id + "_" + str(day) + ".p", "wb"))

        #pickle.dump(valid_pos, open("D:\\ecog_processed\\d_reduced\\valid_pos_" + sbj_id + "_" + str(day) + ".p", "wb"))
        #print(pca.explained_variance_ratio_)

