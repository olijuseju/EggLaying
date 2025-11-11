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

#paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000000'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000001'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000002'))
#paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000003'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000004'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000005'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000006'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000007'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000008'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000009'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000010'))

shape = (128,128)

for path, name_video in paths:

    start_time = time.time()

    # data = np.load(path + name_video + '.npz', allow_pickle=True)
    # lst = data.files
    # for item in lst:
    #     print(item)
    #     print(data[item])

    poses = lib.simplify_video(path, name_video, shape)

    print("--- %s seconds ---" % (time.time() - start_time))

    # path_out = path.replace('egg_laying', 'egg_laying_new')
    # lib.show_video(path_out, name_video, shape)



