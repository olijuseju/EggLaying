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

#print(cv2.__version__)
print('******************************************************* Egg laying detection v4')

paths = []
# Videos originales
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 1/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 2/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 3/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 4/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 5/', '000000'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 6/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 7/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying/Gusano 8/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 9/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 10/', '000005'))

#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/1/', '000002'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/2/', '000003'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/3/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/4/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/5/', '000000'))
##paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/6/', '000004')) #problemas de descarga
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/7/', '000002'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/8/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/9/', '000003'))
#paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/10/', '000003'))

# Videos encuadrados
#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 1/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 2/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 3/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 4/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 5/', '000000'))

#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 6/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 7/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 8/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 9/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 10/', '000005'))

#paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/1/', '000002'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/2/', '000003'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/3/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/4/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/5/', '000000'))
##paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/6/', '000004')) #problemas de descarga
#paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/7/', '000002'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/8/', '000005'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/9/', '000003'))
#paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/10/', '000003'))

paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000000'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000001'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000002'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000003'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000004'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000005'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000006'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000007'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000007'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000008'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000009'))
paths.append(('/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/', '000010'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000001'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000004'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000006'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000007'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000008'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000009'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000010'))



folder_path = '/mnt/Avicemis-Compartido/ASanchez/egg_laying/completos/1/'  # Change this to your target folder
files = os.listdir(folder_path)

print("Files in folder:")
for file in files:
    print(file)

for path, name_video in paths:

    start_time = time.time()

    print('--------------------------path:', path)

    if not os.path.exists(path + "imgs"):
        os.makedirs(path + "imgs")

    # data = np.load(path + name_video + '.npz', allow_pickle=True)
    # lst = data.files
    # for item in lst:
    #     print(item)
    #     print(data[item])

    cap = cv2.VideoCapture(path + name_video + '.mp4')
    print(path + name_video)

    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps:", fps)

    totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print("totalNoFrames:", totalNoFrames)

    durationInSeconds = totalNoFrames / fps
    print("durationInSeconds:", durationInSeconds, "s")

    # start_time = time.time()

    ini_frame = 0
    end_frame = int(totalNoFrames) - 1

    eggs_dist_transform, img_changes_0, noise, gray_end = lib.get_changes_red(path, name_video, cap, ini_frame, end_frame)

    # ini_frame = 16874
    # end_frame = 17436
    intervals = lib.tracking(path, name_video, cap, ini_frame, end_frame, eggs_dist_transform, noise)
    frame_items = []
    for (ini_frame, end_frame, init_pose) in intervals:
        frame_items1 = lib.process_in_detail(path, name_video, cap, ini_frame, end_frame, eggs_dist_transform, img_changes_0, noise, gray_end, init_pose)
        for item in frame_items1:
            frame_items.append(item)
    print('frame_items:', frame_items)

    with open(path + 'metadata_eggs_times.csv', 'w', newline='') as csvfile:
        fieldnames = ['full_data', 'cy', 'cx', 'area', 'ratio', 'dist_skel_egg', 'skel_lenght', 'ratio_skel_lenght_dist_min', 'blue_dist', 'sum_diff']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for items in frame_items:
            for item in items:
                sec = int(item[0] / fps)
                writer.writerow({'full_data': str(datetime.timedelta(seconds=sec)), 'cy': str(item[1]), 'cx': str(item[2]), 'area': str(item[3]), 'ratio': str(item[4]), 'dist_skel_egg': str(item[5]), 'skel_lenght': str(item[6]), 'ratio_skel_lenght_dist_min': str(item[7]), 'blue_dist': str(item[8]), 'sum_diff': str(item[9])})

    with open(path + 'metadata_eggs_frames.csv', 'w', newline='') as csvfile:
        fieldnames = ['frame_num', 'cy', 'cx', 'area', 'ratio', 'dist_skel_egg', 'skel_lenght', 'ratio_skel_lenght_dist_min', 'blue_dist', 'sum_diff']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for items in frame_items:
            for item in items:
                writer.writerow({'frame_num': str(item[0]), 'cy': str(item[1]), 'cx': str(item[2]), 'area': str(item[3]), 'ratio': str(item[4]), 'dist_skel_egg': str(item[5]), 'skel_lenght': str(item[6]), 'ratio_skel_lenght_dist_min': str(item[7]), 'blue_dist': str(item[8]), 'sum_diff': str(item[9])})

    print("--- %s seconds ---" % (time.time() - start_time))