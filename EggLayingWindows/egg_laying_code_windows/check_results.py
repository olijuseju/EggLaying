import cv2
import numpy as np
import datetime
import pandas as pd
import csv
import os
from skimage.morphology import skeletonize
import time
import math
import lib
#import Tkinter

print('******************************************************* Checking egg-laying detection v2')

# Se realiza un proceso de chequeo del fichero check_file

check_file = 'none'
#check_file = 'metadata_eggs_gt.csv'
# check_file = 'metadata_eggs_times.csv'
#check_file = 'metadata_eggs_frames.csv'
#check_file = 'metadata_eggs_frames_gt.csv'
# check_file = 'metadata_eggs_test.csv'
#check_file = 'metadata_eggs_gt.xlsx'

# Times are labelled with seconds precision (and these videos are saved at 25 fps)
#frames_before = 25
frames_before = 2
frames_after = 125
#frames_after = 0

paths = []
# Videos originales
#paths.append(('/home/antonio/Descargas/egg_laying/Gusano 1/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/Gusano 2/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/Gusano 3/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/Gusano 4/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/Gusano 5/', '000000'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 6/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 7/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying/Gusano 8/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying/Gusano 9/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 10/', '000005'))

#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/1/', '000002'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/2/', '000003'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/3/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/5/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/7/', '000002'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/8/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/9/', '000003'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/10/', '000003'))

# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000001'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000002'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000004'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000006'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000007'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000008'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000009'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000010'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000001'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000004'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000006'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000007'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000008'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000009'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000010'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000011'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000012'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000013'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000014'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000015'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000001'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000003'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000004'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000005'))
#
#paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000001'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000004'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000005'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000001'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000003'))#paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000004'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000005'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000001'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000002'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000003'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000004'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000005'))

for path, name_video in paths:

    print('--------------------------', path)
    if not os.path.exists(path+name_video+"_imgs"):
        os.makedirs(path+name_video+"_imgs")

    cap = cv2.VideoCapture(path + name_video + '.mp4')

    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps:", fps)

    totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print("totalNoFrames:", totalNoFrames)

    durationInSeconds = totalNoFrames / fps
    print("durationInSeconds:", durationInSeconds, "s")

    ini_frame = 0
    end_frame = int(totalNoFrames) - 1

    eggs_dist_transform, img_changes_0, noise = lib.get_changes_red(path, cap, ini_frame, end_frame)

    #data = np.load(path + name_video + '.npz')
    #print("data:", data)

    #if os.path.exists(path + "img_background.bmp"):
    #    img_background = cv2.imread(path + "img_background.bmp")

    if os.path.exists(path+check_file):

        if os.path.splitext(check_file)[1] == '.csv':
            df = pd.read_csv(path+check_file)
        else:
            df = pd.read_excel(path+check_file, index_col=None, header=None)
            df.columns = ['full_data']

        df_wd = df.drop_duplicates()
        #print(df.to_string())

        time_items = []
        frame_items =[]
        for ind in df_wd.index:
            if 'full_data' in df:
                if type(df['full_data'].iloc[ind]) == datetime.time:
                    egg_time = pd.to_timedelta(str(df['full_data'].iloc[ind]))
                else:
                    egg_time = pd.to_timedelta(df['full_data'].iloc[ind])
                print('--------------------------egg_time: ', egg_time)

                egg_frame = int((fps * egg_time.total_seconds()) + 0.5)
            else:
                egg_frame = int(df['frame_num'].iloc[ind])
                print('--------------------------egg_frame: ', egg_frame)

            ini_frame = max(0, egg_frame - int(frames_before))
            end_frame = min(totalNoFrames, egg_frame + int(frames_after))
            frame_items = lib.process_in_detail(path, name_video, cap, ini_frame, end_frame, eggs_dist_transform, img_changes_0, noise, show = True)
            print('frame_items:', frame_items)

    else:
        print(path + check_file + " file doesn't exist")

        egg_frame = int(input("Which egg_frame do you want to check? "))
        ini_frame = max(0, egg_frame - int(frames_before))
        end_frame = min(totalNoFrames, egg_frame + int(frames_after))
        frame_items = lib.process_in_detail(path, name_video, cap, ini_frame, end_frame, eggs_dist_transform, img_changes_0, noise, show=True)
        print('frame_items:', frame_items)

    cap.release()
