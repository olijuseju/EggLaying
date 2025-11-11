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

import concurrent.futures

#print(pd.__version__)
print('******************************************************* Egg laying detection v5')

paths = []
# # Videos originales
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 1/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 2/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 3/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 4/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/Gusano 5/', '000000'))

# # paths.append(('/home/antonio/Descargas/egg_laying/Gusano 6/', '000005'))
# # paths.append(('/home/antonio/Descargas/egg_laying/Gusano 7/', '000005'))
# # paths.append(('/home/antonio/Descargas/egg_laying/Gusano 8/', '000005'))
# # paths.append(('/home/antonio/Descargas/egg_laying/Gusano 9/', '000005'))
# # paths.append(('/home/antonio/Descargas/egg_laying/Gusano 10/', '000005'))

# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/1/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/2/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/5/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/7/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/8/', '000005'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/9/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/gusanos borde/10/', '000003'))
# #
# paths.append(('/home/antonio/Descargas/egg_laying/completos/1/', '000000'))
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
# # #
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000001'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/2/', '000002'))
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
# #
paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000000'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000001'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000002'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000003'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000004'))
paths.append(('/home/antonio/Descargas/egg_laying/completos/3/', '000005'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000001'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000004'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/4/', '000005'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000001'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000004'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/5/', '000005'))
#
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000000'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000001'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000002'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000003'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000004'))
# paths.append(('/home/antonio/Descargas/egg_laying/completos/6/', '000005'))

simplify = True

# with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
#
#     start_time = time.time()
#
#     # Submit each computation task to the thread pool
#     futures = [executor.submit(lib.video_process, path, name_video, simplify) for (path, name_video) in paths]
#
#     # Wait for all tasks to complete and retrieve the results
#     results = [future.result() for future in concurrent.futures.as_completed(futures)]
#
#     # Print the results
#     print(results)
#
#     if len(paths) > 0:
#         print("--- %s minutes per video ---" % ((time.time() - start_time)/(len(paths)*60)))

new_paths = []
name_videos = []

for (path, name_video) in paths:
    if not path in new_paths:
        new_paths.append(path)
        name_videos.append([name_video])
    else:
        for i, new_path in enumerate(new_paths):
            if path == new_path:
                name_videos[i].append(name_video)
                break

for i, path in enumerate(new_paths):
    evaluator = lib.Evaluator(path, name_videos[i])
    evaluator.show_results()

