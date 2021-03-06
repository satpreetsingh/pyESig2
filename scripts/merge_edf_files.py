import pyedflib
import pandas
import numpy as np
from vid.video_sync.vid_start_end import get_disconnected_times
from datetime import datetime, timedelta
from copy import copy
import pdb
import gc

sbj_id = "c95c1e82"
conversion_file = "/home/nancy/Documents/data_release/%s.csv" % sbj_id
disconnect_times_dir = "/home/nancy/Documents/disconnect_times/"
orig_edf_dir = "/data/decrypted_edf/%s/" % sbj_id
save_dir = "/space/nancy/data_by_day/"

def get_sample_len(time1, time2):
    return max(0, int((time2-time1).total_seconds()*1000))

conversion = pandas.read_csv(conversion_file)

for d in range(conversion.shape[0]):
    orig_files = ["%s/%s.edf" % (orig_edf_dir, orig_file) for orig_file in [conversion["file1"][d],conversion["file2"][d],conversion["file3"][d]] if not isinstance(orig_file, float)]
    start_end_times = [get_disconnected_times("%s/%s.txt" % (disconnect_times_dir, orig_file))[:2]
                       for orig_file in [conversion["file1"][d],conversion["file2"][d],conversion["file3"][d]] if not isinstance(orig_file, float)]
    final_start_time = datetime.strptime("01-%02i-1000 " % conversion["day"][d] + conversion["start_time"][d], '%m-%d-%Y %H:%M:%S:%f')
    final_end_time = datetime.strptime("01-%02i-1000 " % conversion["day"][d] + conversion["end_time"][d], '%m-%d-%Y %H:%M:%S:%f')


    final_start_time_orig = datetime.strptime(conversion["date"][d] + " " + conversion["start_time"][d], '%m/%d/%Y %H:%M:%S:%f')
    final_end_time_orig = datetime.strptime(conversion["date"][d] + " " + conversion["end_time"][d], '%m/%d/%Y %H:%M:%S:%f')

    # Set up final edf file
    edf_files = [pyedflib.EdfReader(file) for file in orig_files]
    n_channels = edf_files[0].getSignalLabels().index('ECGR')
    edf_out = pyedflib.EdfWriter("%s/%s_day_%i.edf" % (save_dir, sbj_id, conversion["day"][d]), n_channels)

    # De-identify date of patient stay and update start time
    edf_out.setHeader(edf_files[0].getHeader())
    edf_out.setStartdatetime(final_start_time)

    # Set signal header
    edf_out.setSignalHeaders(edf_files[0].getSignalHeaders()[1:n_channels+1])
    for c in xrange(n_channels):
        edf_out.setSamplefrequency(c, 1000)
    # write data
    physical_min = edf_files[0].getPhysicalMinimum(1)
    main_data = []
    gc.collect()
    for channel in range(1, n_channels+1):
        chan_data = np.array([physical_min]*get_sample_len(final_start_time_orig-timedelta(microseconds=final_start_time_orig.microsecond), start_end_times[0][0]))
        for f, file in enumerate(edf_files):
            print "loading channel %i of file %s" % (channel, orig_files[f])
            if final_start_time_orig > start_end_times[f][0]:
                chan_data = np.hstack([chan_data, file.readSignal(channel)[get_sample_len(start_end_times[f][0], final_start_time_orig):]])
            elif final_end_time_orig < start_end_times[f][1]:
                chan_data = np.hstack([chan_data, file.readSignal(channel)[:get_sample_len(start_end_times[f][0], final_end_time_orig)]])
            else:
                chan_data = np.hstack([chan_data, file.readSignal(channel)])
            if f+1 < len(start_end_times):
                chan_data = np.hstack([chan_data, np.array([physical_min]*get_sample_len(start_end_times[f][1], start_end_times[f+1][0]))])
        chan_data = copy(chan_data[:(len(chan_data)/3-len(chan_data)/3%1000)])
        main_data.append(chan_data)

    edf_out.writeSamples(main_data)

    main_data = []
    gc.collect()
    for channel in range(1, n_channels+1):
        chan_data = np.array([physical_min]*get_sample_len(final_start_time_orig-timedelta(microseconds=final_start_time_orig.microsecond), start_end_times[0][0]))
        for f, file in enumerate(edf_files):
            print "loading channel %i of file %s" % (channel, orig_files[f])
            if final_start_time_orig > start_end_times[f][0]:
                chan_data = np.hstack([chan_data, file.readSignal(channel)[get_sample_len(start_end_times[f][0], final_start_time_orig):]])
            elif final_end_time_orig < start_end_times[f][1]:
                chan_data = np.hstack([chan_data, file.readSignal(channel)[:get_sample_len(start_end_times[f][0], final_end_time_orig)]])
            else:
                chan_data = np.hstack([chan_data, file.readSignal(channel)])
            if f+1 < len(start_end_times):
                chan_data = np.hstack([chan_data, np.array([physical_min]*get_sample_len(start_end_times[f][1], start_end_times[f+1][0]))])
        chan_data = copy(chan_data[(len(chan_data)/3-len(chan_data)/3%1000):(2*len(chan_data)/3-2*len(chan_data)/3%1000)])
        main_data.append(chan_data)
    edf_out.writeSamples(main_data)

    main_data = []
    gc.collect()
    for channel in range(1, n_channels+1):
        chan_data = np.array([physical_min]*get_sample_len(final_start_time_orig-timedelta(microseconds=final_start_time_orig.microsecond), start_end_times[0][0]))
        for f, file in enumerate(edf_files):
            print "loading channel %i of file %s" % (channel, orig_files[f])
            if final_start_time_orig > start_end_times[f][0]:
                chan_data = np.hstack([chan_data, file.readSignal(channel)[get_sample_len(start_end_times[f][0], final_start_time_orig):]])
            elif final_end_time_orig < start_end_times[f][1]:
                chan_data = np.hstack([chan_data, file.readSignal(channel)[:get_sample_len(start_end_times[f][0], final_end_time_orig)]])
            else:
                chan_data = np.hstack([chan_data, file.readSignal(channel)])
            if f+1 < len(start_end_times):
                chan_data = np.hstack([chan_data, np.array([physical_min]*get_sample_len(start_end_times[f][1], start_end_times[f+1][0]))])
        chan_data = copy(chan_data[(2*len(chan_data)/3-2*len(chan_data)/3%1000):])
        main_data.append(chan_data)
    edf_out.writeSamples(main_data)

    edf_out.close()
    for file in edf_files:
        file._close()
