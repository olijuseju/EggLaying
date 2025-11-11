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
import shutil

print('******************************************************* Dataset v2')

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

# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/1/', '000002'))
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
# paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 1/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 2/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 3/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 4/', '000000'))
paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 5/', '000000'))
#
# paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 6/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 7/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 8/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 9/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/Gusano 10/', '000005'))
#
# paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/1/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/2/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/3/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/4/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/5/', '000000'))
# #paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/6/', '000004')) #problemas de descarga
# paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/7/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/8/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/9/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying_new/gusanos borde/10/', '000003'))

check_file = 'metadata_eggs_frames.csv'

for path, name_video in paths:

    print('--------------------------path:', path)

    if not os.path.exists(path + "TP"):
        #shutil.rmtree(path + "TP")
        os.makedirs(path + "TP")

    if not os.path.exists(path + "TN"):
        #shutil.rmtree(path + "TN")
        os.makedirs(path + "TN")

    cap = cv2.VideoCapture(path + name_video + '.mp4')

    fps = cap.get(cv2.CAP_PROP_FPS)
    #print("fps:", fps)

    totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    #print("totalNoFrames:", totalNoFrames)

    durationInSeconds = totalNoFrames / fps
    #print("durationInSeconds:", durationInSeconds, "s")

    ini_frame = 0
    end_frame = int(totalNoFrames) - 1

    _, img_changes_0 = lib.get_changes_red(path, cap, ini_frame, end_frame)

    if os.path.exists(path+check_file):
        df = pd.read_csv(path+check_file)
        df_wd = df.drop_duplicates()

        for ind in df_wd.index:
            egg_frame = int(df['frame_num'].iloc[ind])
            print('--------------------------egg_frame: ', egg_frame)

            n_frame = max(0, egg_frame - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, n_frame)
            ret, img = cap.read()
            gray_ant = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            ret, img = cap.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            diff = gray_ant.astype(int) - gray.astype(int)
            #pts_diff = np.where(diff >= 30)
            pts_diff = np.where(diff >= 23) # v6
            img_seg_dilated, img_seg, boxes = lib.get_segmentation(img, pts_diff)
            img_res = cv2.bitwise_and(img, img, mask=img_seg_dilated)

            #cv2.imshow("img_res", img_res)
            #cv2.waitKey(0)
            #cv2.destroyAllWindows()

            for idx, box in enumerate(boxes):
                # Recorte de imágenes según box
                x_ini = box[0, 1]  # y
                y_ini = box[0, 0]  # x
                x_fin = box[1, 1]  # y+h
                y_fin = box[2, 0]  # x+w

                diff_recortada = diff[x_ini:x_fin, y_ini:y_fin]
                pts_diff_recortada = np.where(diff_recortada >= 30)
                img_changes_pos = np.zeros((x_fin - x_ini, y_fin - y_ini), np.uint8)
                img_changes_pos[pts_diff_recortada] = 255

                img_result = np.zeros((x_fin-x_ini, y_fin-y_ini, 3), np.uint8)
                img_result[:, :, 0] = img_changes_0[x_ini:x_fin, y_ini:y_fin]
                img_result[:, :, 1] = 255-gray[x_ini:x_fin, y_ini:y_fin]
                img_result[:, :, 2] = 255-gray_ant[x_ini:x_fin, y_ini:y_fin] #img_changes_pos

                # resize image
                width = int(img_result.shape[1] * 8)
                height = int(img_result.shape[0] * 8)
                img_result_resized = cv2.resize(img_result, (width, height)) #, interpolation=cv2.INTER_AREA

                img_name = str(n_frame) + "_" + str(idx)
                #cv2.namedWindow(img_name, cv2.WINDOW_NORMAL)
                #cv2.resizeWindow(img_name, width, height)
                cv2.imshow(img_name, img_result_resized)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

                cv2.imwrite(path + "TP\\" + img_name + ".bmp", img_result)


