import cv2
import numpy as np
import datetime
import pandas as pd
import csv
import os
from skimage.morphology import skeletonize
import time
import math

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
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 8/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 9/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 10/', '000005'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/1/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/2/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/3/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/5/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/7/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/8/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/9/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/10/', '000003'))

paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000000'))
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

for path, name_video in paths:

    path_out = path.replace('egg_laying', 'egg_laying_new')

    # data = np.load(path + name_video + '.npz', allow_pickle=True)
    # lst = data.files
    # for item in lst:
    #     print(item)
    #     print(data[item])

    cap = cv2.VideoCapture(path + name_video + '.mp4')

    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps:", fps)

    totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print("totalNoFrames:", totalNoFrames)

    durationInSeconds = totalNoFrames / fps
    print("durationInSeconds:", durationInSeconds, "s")

    n_frame = 0
    end_frame = totalNoFrames
    #end_frame = 50
    cap.set(cv2.CAP_PROP_POS_FRAMES, n_frame)

    while (n_frame < end_frame) and (cap.isOpened()):
        #start_time = time.time()
        print(path, '--------------------------n_frame: ', n_frame)
        ret, img = cap.read()
        # cv2.imshow("img", img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #img_aux = gray.copy()
        if n_frame == 0:
            if os.path.exists(path + name_video + "_img_result_tracking.bmp"):
                img_result = cv2.imread(path + name_video + "_img_result_tracking.bmp")
                img_result_blue = img_result[:,:,0]

                #cv2.imshow("img_result", img_result)
                #cv2.waitKey(0)
                # cv2.destroyAllWindows()

                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (63, 63), (3, 3))
                img_result_blue = cv2.dilate(img_result_blue, kernel, iterations=1)

                _, contours, hierarchy = cv2.findContours(img_result_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                for contour in contours:

                    #cv2.drawContours(img_aux, [contour], -1, 0, thickness=cv2.FILLED)

                    r = cv2.boundingRect(contour)
                    print('roi:', r)
            else:
                # Select ROI
                r = cv2.selectROI("Select a roi", gray)
                #print(r)

            np.save(path_out + name_video + '.npy', r)

            # Crop gray image in the first frame
            # cropped_gray = gray[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]
            #print(cropped_gray.shape, (int(r[2], int(r[3]))))
            # img_background = cropped_gray.astype(np.float)
            # count_frames = 1

            # Crea video nuevo
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            #fourcc = cv2.VideoWriter_fourcc(*'h264') #todo este codec no está instalado
            out = cv2.VideoWriter(path_out + name_video + '.mp4', fourcc, fps, (int(r[2]), int(r[3])), 0)

            # gray_ant = cropped_gray.copy()

        # Crop gray image
        gray = gray[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]

        if out.isOpened():
            out.write(gray)
        else:
            print('Error no se puede crear el vídeo...')
            break

        # diff = gray_ant.astype(int) - gray.astype(int)
        # pts_diff = np.where(diff >= 30)
        # if len(pts_diff[0]) > 0:
        #     img_background = img_background + gray.astype(float)
        #     count_frames = count_frames +1
        #
        #     #img_background_act = (img_background/float(n_frame+1)).astype(np.uint8)
        #     #cv2.imshow('gray', gray)
        #     #print('Waiting! Press key...')
        #     #if cv2.waitKey(0) & 0xFF == ord('q'):
        #     #    break

        n_frame = n_frame + 1
        # gray_ant = gray.copy()

        #print("--- %s seconds ---" % (time.time() - start_time))

    # img_background_act = (img_background / float(count_frames)).astype(np.uint8)
    # cv2.imwrite(path_out + "img_background.bmp", img_background_act)
    # cv2.destroyAllWindows()
    # cap.release()
    # out.release()
