import cv2
import numpy as np
import datetime
import pandas as pd
import csv
import os
from skimage.morphology import skeletonize
import time
import math
import statistics
import random
import pandas as pd

font = cv2.FONT_HERSHEY_SIMPLEX
org = (50, 50)
fontScale = 1
color = (255, 0, 0)
thickness = 2

def is_anyPoint_in_rect(pts_diff, rect):
    is_anyPoint_in_rect = False

    (x, y, w, h) = rect
    #(x, y, w, h) = (x-2, y-2, w+4, h+4) # marco de anchura 2 de seguridad
    pts_diff_x = pts_diff[1]
    pts_diff_y = pts_diff[0]
    for point in zip(pts_diff_x, pts_diff_y):
        diff_x = point[0] - x + 2
        diff_y = point[1] - y + 2
        if ( diff_x > 0) and (diff_x < w+4) and ( diff_y > 0) and (diff_y < h+4):
            is_anyPoint_in_rect = True

    return is_anyPoint_in_rect


def get_noise(gray):
    #noise = cv2.inRange(gray, 0, 160)
    noise = cv2.inRange(gray, 0, 110)
    kernel = np.ones((5, 5), np.uint8)
    noise = cv2.morphologyEx(noise, cv2.MORPH_CLOSE, kernel)
    return noise


# Se segmentan las cajas que tienen un objeto oscuro de un determinado tamaño
# y además dentro de ella se ha detectado movimiento con respecto a la imagen anterior
def get_segmentation(img, pts_diff, intentos, worm_detected):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if intentos > 1:
        ## segmentation problems solution (bordes 7 y gusano 8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        gray = cv2.erode(gray, kernel)
    # else:
    #     kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    #     gray = cv2.erode(gray, kernel)

    sure_fg = cv2.inRange(gray, 0, 110) # Rango de valores de gusano seguros

    sure_bg = cv2.inRange(gray, 165, 256)  # Rango de valores altos de fondo seguros
    #sure_bg = cv2.inRange(gray, 160, 256)  # Rango de valores altos de fondo seguros
    #sure_bg = cv2.inRange(gray,170,256) # Rango de valores altos de fondo seguros
    #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7), (3, 3))
    #sure_bg = cv2.erode(sure_bg, kernel, iterations=2)

    sure_bg[sure_bg==255] = 128
    marker = cv2.add(sure_fg, sure_bg)

    # cv2.imshow("marker", marker)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    marker32 = np.int32(marker)
    cv2.watershed(img, marker32)
    m = cv2.convertScaleAbs(marker32)

    ret, res = cv2.threshold(m, 129, 255, cv2.THRESH_BINARY)

    #cv2.imshow("res", res)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7), (3, 3))
    res_dilated = cv2.dilate(res, kernel, iterations=2)

    #cv2.imshow("res_dilated", res_dilated)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

    # # Me quedo con el contorno de más área para filtrar ruido
    #_, contours, hierarchy = cv2.findContours(res_dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours, hierarchy = cv2.findContours(res_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # # dibujo la máscara
    height, width = res.shape[0:2]
    res_dilated = np.zeros((height, width), np.uint8)

    boxes = []
    for contour in contours:
        area = cv2.contourArea(contour)
        rect = cv2.boundingRect(contour)
        #if (area > 600.0) and (area < 3000.0):
        if (area > 1000.0) and (area < 3000.0):
            if (is_anyPoint_in_rect(pts_diff, rect)) or ((len(pts_diff[0]) == 0) and not worm_detected):
                #print('area worm:', area)
                # print('pts_diff:',pts_diff)
                # print('rect:', rect)

                cv2.drawContours(res_dilated, [contour], -1, 255, thickness=cv2.FILLED)
                (x, y, w, h) = rect
                x = max(0, x-2)
                y = max(0, y-2)
                yh = min(height-1, y + h + 4)
                xw = min(width-1, x + w + 4)
                #(x, y, w, h) = (x-2, y-2, w+4, h+4) # marco de anchura 2 de seguridad
                #box = np.asarray([[x, y],[x, y+h],[x+w, y+h],[x+w, y]])
                box = np.asarray([[x, y], [x, yh], [xw, yh], [xw, y]])
                box = np.int0(box)
                boxes.append(box)

                #rect = cv2.minAreaRect(contour)
                #box = cv2.boxPoints(rect)
                #box = np.int0(box)

    return res_dilated, res, boxes


def borra_gusanos(path, name_video, img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #path_name_video = os.path.join(path, name_video)
    #cv2.imwrite(path_name_video + "_imgs/gray.bmp", gray)

    sure_fg = cv2.inRange(gray, 0, 110) # Rango de valores de gusano seguros
    sure_bg = cv2.inRange(gray, 165, 256)  # Rango de valores altos de fondo seguros

    sure_bg[sure_bg==255] = 128
    
    ######################## CODIGO JOSE ###################################
    #print(f"cv2.countNonZero(sure_fg):  {cv2.countNonZero(sure_fg)}")
    if cv2.countNonZero(sure_fg) < 1000:  # Ajustable
        print(f"[INFO] No se detectó gusano en {name_video}. Imagen no modificada.")
        return gray
        
    ####################### FIN CODIGO JOSE ################################
        
    marker = cv2.add(sure_fg, sure_bg)
    # cv2.imshow("marker", marker)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    marker32 = np.int32(marker)
    cv2.watershed(img, marker32)
    m = cv2.convertScaleAbs(marker32)

    ret, res = cv2.threshold(m, 129, 255, cv2.THRESH_BINARY)
    #cv2.imshow("res", res)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    res_dilated = cv2.dilate(res, kernel, iterations=2)

    contours, hierarchy = cv2.findContours(res_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for contour in contours:
        area = cv2.contourArea(contour)
        #if (area > 800) and (area < 1250):
        if (area > 600) and (area < 1250):
            print(path, name_video, 'area worm deleted in gray_ini:', area)
            cv2.drawContours(gray, [contour], -1, 170, thickness=cv2.FILLED)
            #cv2.drawContours(gray, [contour], -1, 255, thickness=cv2.FILLED)

    return gray

def neighbours(skel,x,y):
    neighbours = []

    if skel[x-1,y-1] == 255:
        neighbours.append((y-1, x-1))
    if skel[x-1,y] == 255:
        neighbours.append((y, x-1))
    if skel[x-1,y+1] == 255:
        neighbours.append((y+1, x-1))
    if skel[x,y-1] == 255:
        neighbours.append((y-1, x))
    if skel[x,y+1] == 255:
        neighbours.append((y+1, x))
    if skel[x+1,y-1] == 255:
        neighbours.append((y-1, x+1))
    if skel[x+1,y] == 255:
        neighbours.append((y, x+1))
    if skel[x+1, y+1] == 255:
        neighbours.append((y+1, x+1))

    return neighbours


def find_index(p, points):
    try:
        index = points.index(p)
    except ValueError:
        index = -1
    return index


def expande_rama(rama, neights, skelPoints, skelPoints_neighs, cruces, endPoints):

    if len(rama) >= 2:
        p_ant = rama[-2]
    else:
        p_ant = rama[-1]
    for p in neights:
        if not ((p[0] == p_ant[0]) and (p[1] == p_ant[1])):
            index = find_index(p, cruces)
            if index > -1:
                rama.append(cruces[index])
                return rama
            else:
                index = find_index(p, endPoints)
                if index > -1:
                    rama.append(endPoints[index])
                    return rama
                else:
                    index = find_index(p, skelPoints)
                    if index > -1:
                        rama.append(skelPoints[index])
                        rama = expande_rama(rama, skelPoints_neighs[index], skelPoints, skelPoints_neighs, cruces, endPoints)
        else:
            continue

    return rama


def is_in_ramas(rama, ramas):
    is_in_ramas = False
    if len(rama) > 0:
        p0 = rama[0]
        p1 = rama[-1]
        for r in ramas:
            if len(rama) == len(r):
                p2 = r[0]
                p3 = r[-1]
                if ((p0[0] == p2[0]) and (p0[1] == p2[1]) and (p1[0] == p3[0]) and (p1[1] == p3[1])) or ((p0[0] == p3[0]) and (p0[1] == p3[1]) and (p1[0] == p2[0]) and (p1[1] == p2[1])):
                    if len(r) <= 2:
                        is_in_ramas = True
                        break
                    else:
                        p0_ = rama[1]
                        p1_ = rama[-2]
                        p2_ = r[1]
                        p3_ = r[-2]
                        if ((p0_[0] == p2_[0]) and (p0_[1] == p2_[1]) and (p1_[0] == p3_[0]) and (p1_[1] == p3_[1])) or ((p0_[0] == p3_[0]) and (p0_[1] == p3_[1]) and (p1_[0] == p2_[0]) and (p1_[1] == p2_[1])):
                            is_in_ramas = True
                            break

    return is_in_ramas


def get_rama_length(r):
    rama_lengh = 0
    if len(r) > 0:
        p_ant = r[0]
        for p in r:
            dx = p_ant[0] - p[0]
            dy = p_ant[1] - p[1]
            dist = math.sqrt((dx*dx)+(dy*dy))
            rama_lengh = rama_lengh + dist
            p_ant = p

    return rama_lengh


def get_solapamiento(rama, skelPoints_ant):

    skel_length = 0
    skel_ant_length = 0
    solapamientos = []

    for idx, (x_ini, y_ini) in enumerate(rama):
        if idx == 0:
            x_ini_ant = x_ini
            y_ini_ant = y_ini

        dx = (x_ini - x_ini_ant)
        dy = (y_ini - y_ini_ant)
        skel_length += math.sqrt((dx * dx) + (dy * dy))
        x_ini_ant = x_ini
        y_ini_ant = y_ini

        min_dist = 999999
        for idx1, (x1_ini, y1_ini) in enumerate(skelPoints_ant):
            if idx1 == 0:
                x1_ini_ant = x1_ini
                y1_ini_ant = y1_ini
            if idx == 0:
                dx = (x1_ini - x1_ini_ant)
                dy = (y1_ini - y1_ini_ant)
                skel_ant_length += math.sqrt((dx * dx) + (dy * dy))
                x1_ini_ant = x1_ini
                y1_ini_ant = y1_ini

            dx = (x_ini - x1_ini)
            dy = (y_ini - y1_ini)
            dist_act = math.sqrt((dx * dx) + (dy * dy))
            if dist_act < min_dist:
                min_dist = dist_act
        if min_dist < 4:
            solapamientos.append((idx,idx1))

    return skel_length, skel_ant_length, solapamientos


def get_solapamiento_lenght(rama, skelPoints_ant):

    solapamiento_lenght = 0
    skelPoints_ant_copy = skelPoints_ant.copy()

    if len(rama) > 8:
        for (x_ini, y_ini) in rama[3:-3]:
            min_dist = 999999
            for ind,(x1_ini, y1_ini) in enumerate(skelPoints_ant_copy):
                dx = (x_ini - x1_ini)
                dy = (y_ini - y1_ini)
                dist_act = math.sqrt((dx * dx) + (dy * dy))
                if dist_act < min_dist:
                    min_dist = dist_act
                    ind_min = ind
            if min_dist < 4:
                solapamiento_lenght +=1
                del skelPoints_ant_copy[ind_min]
            # solapamiento_lenght += min_dist
            # del skelPoints_ant_copy[ind_min]

    return solapamiento_lenght


def solapan(ramas, skelPoints_ant):
    hay_solapamiento = False

    if len(skelPoints_ant) > 0:
        for rama in ramas:
            solapamiento = get_solapamiento_lenght(rama, skelPoints_ant)
            if solapamiento > 0:
                hay_solapamiento = True
                break
    return hay_solapamiento


def get_distancia_red(rama, red_dist_transform):

    min_dist = 99999999
    for (x_ini, y_ini) in rama:
        dist = red_dist_transform[y_ini, x_ini]
        if dist < min_dist:
            min_dist = dist
    return min_dist


def get_distancias_red(ramas, red_dist_transform):

    distancias = []
    max_dist = 0
    min_dist = 99999999
    for index, rama in enumerate(ramas):
        dist = get_distancia_red(rama, red_dist_transform)
        distancias.append(dist)
        if dist > max_dist:
            max_dist = dist
        if dist < min_dist:
            min_dist = dist

    for index, dist in enumerate(distancias):
        if max_dist > min_dist:
            distancias[index] = 1 - ((distancias[index]-min_dist) / (max_dist-min_dist))
        else:
            distancias[index] = 1

    return distancias, max_dist, min_dist


def get_distancia_red_normalizada(rama, red_dist_transform, max_dist, min_dist):

    dist = get_distancia_red(rama, red_dist_transform)
    if max_dist > min_dist:
        dist_normalizada = (1 - ((dist - min_dist) / (max_dist - min_dist))) * len(rama)
    else:
        dist_normalizada = len(rama)

    return dist_normalizada


def concatena_ramas(rama, ramas, skelPoints_ant, red_dist_transform, cont):

    max_length = 0
    soluciones = []
    #print(f"len(rama){len(rama)}")
    #print(f"len(ramas){len(ramas)}")
    cont+=1
    for index, r in enumerate(ramas):
        #print(f"index{index}")
        #print(f"len(rama){len(rama)}")
        #print(f"len(r){len(r)}")
        if (len(rama) > 0) and (len(r) > 0) and (len(r) < 20) and (cont<1000):
        
            p0 = rama[0]
            p1 = rama[-1]

            p2 = r[0]
            p3 = r[-1]

            if ((p1[0] == p2[0]) and (p1[1] == p2[1]) and ((p0[0] != p3[0]) or (p0[1] != p3[1]))):
                new_rama = rama[0:-1] + r
                new_ramas = ramas.copy()
                del new_ramas[index]
                hay_solapamiento = solapan(new_ramas, skelPoints_ant)
                soluciones.append(concatena_ramas(new_rama, new_ramas, skelPoints_ant, red_dist_transform,cont))
            elif ((p0[0] == p3[0]) and (p0[1] == p3[1]) and ((p1[0] != p2[0]) or (p1[1] != p2[1]))):
                new_rama = r[0:-1] + rama
                new_ramas = ramas.copy()
                del new_ramas[index]
                hay_solapamiento = solapan(new_ramas, skelPoints_ant)
                soluciones.append(concatena_ramas(new_rama, new_ramas, skelPoints_ant, red_dist_transform,cont))
            elif ((p0[0] == p2[0]) and (p0[1] == p2[1]) and ((p1[0] != p3[0]) or (p1[1] != p3[1]))):
                new_rama = r[::-1][0:-1] + rama
                new_ramas = ramas.copy()
                del new_ramas[index]
                hay_solapamiento = solapan(new_ramas, skelPoints_ant)
                soluciones.append(concatena_ramas(new_rama, new_ramas, skelPoints_ant, red_dist_transform,cont))
            elif ((p1[0] == p3[0]) and (p1[1] == p3[1]) and ((p0[0] != p2[0]) or (p0[1] != p2[1]))):
                new_rama = rama[0:-1] + r[::-1]
                new_ramas = ramas.copy()
                del new_ramas[index]
                soluciones.append(concatena_ramas(new_rama, new_ramas, skelPoints_ant, red_dist_transform,cont))
            elif (p1[0] == p2[0]) and (p1[1] == p2[1]):
                new_rama = rama[0:-1] + r
                new_ramas = ramas.copy()
                del new_ramas[index]
                hay_solapamiento = solapan(new_ramas, skelPoints_ant)
                soluciones.append(concatena_ramas(new_rama, new_ramas, skelPoints_ant, red_dist_transform,cont))

    #if not hay_solapamiento:
    distancias, max_dist, min_dist = get_distancias_red(soluciones, red_dist_transform)

    for solucion in soluciones:
        length_sol = get_solapamiento_lenght(solucion, skelPoints_ant) + (get_distancia_red_normalizada(solucion, red_dist_transform, max_dist, min_dist)/3)

        #if (length_sol > max_length) and (length_sol < 105):
        if (length_sol > max_length):
            max_length = length_sol
            rama = solucion

    return rama


def expand_group(group, dists):
    row = group[-1]
    new_indices_group = np.where(dists[row, :] < 2)
    for index in new_indices_group[0]:
        if not index in group:
            group.append(index)
            group = expand_group(group, dists)

    return group


def find_groups(cruces):
    groups = []
    dists = np.ones((len(cruces),len(cruces))) * 999999
    for index1 in range(0,len(cruces)-1):
        cruce1 = cruces[index1]
        for index2 in range(index1+1, len(cruces)):
            cruce2 = cruces[index2]
            dx = cruce1[0]-cruce2[0]
            dy = cruce1[1]-cruce2[1]
            dists[index1, index2] = math.sqrt((dx*dx)+(dy*dy))

    for row in range(0,len(cruces)):
        new_group = True
        for g in groups:
            if row in g:
                new_group = False

        if new_group:
            group = expand_group([row], dists)
            groups.append(group)

    return groups


def simplifica(cruces, cruces_neighs):
    new_cruces = []
    new_cruces_neighs = []
    groups = find_groups(cruces)
    for group in groups:
        if len(group) == 1:
            new_cruces.append(cruces[group[0]])
            new_cruces_neighs.append(cruces_neighs[group[0]])
        else:
            new_cruce_x, new_cruce_y = 0, 0
            new_cruce_neighs = []

            cruces_coor = []
            for index in group:
                cruces_coor.append(cruces[index])

            for index in group:
                new_cruce_x = new_cruce_x + cruces[index][0]
                new_cruce_y = new_cruce_y + cruces[index][1]

                for neigh_coor in cruces_neighs[index]:
                    if not neigh_coor in cruces_coor:
                        new_cruce_neighs.append(neigh_coor)

            new_cruce_x = int(new_cruce_x / len(group))
            new_cruce_y = int(new_cruce_y / len(group))
            new_cruces.append((new_cruce_x, new_cruce_y))
            new_cruces_neighs.append(new_cruce_neighs)

    return groups, new_cruces, new_cruces_neighs


def change_coor(skelPoints_neighs, cruces_coor, new_cruce_coor):

    for index1, skelPoints_neigh in enumerate(skelPoints_neighs):
        for index2, skelPoint_neigh in enumerate(skelPoints_neigh):
            if skelPoint_neigh in cruces_coor:
                skelPoints_neighs[index1][index2] = new_cruce_coor

    return skelPoints_neighs


def invert_rama(rama, skelPoints_ant):

    invert = False
    indices = []
    for (x_ini, y_ini) in rama:
        min_dist = 999999
        ind2_min = -1
        for ind2, (x1_ini, y1_ini) in enumerate(skelPoints_ant):
            dx = (x_ini - x1_ini)
            dy = (y_ini - y1_ini)
            dist_act = math.sqrt((dx * dx) + (dy * dy))
            if dist_act < min_dist:
                min_dist = dist_act
                ind2_min = ind2
        indices.append(ind2_min)

    suma = 0
    for idx, ind2 in enumerate(indices):
        if idx > 0:
            if (ind2 - ind2_ant) > 0:
                suma += 1
            elif (ind2 - ind2_ant) < 0:
                suma -= 1
        ind2_ant = ind2

    if suma == 0:
        if len(rama) > 0 and len(skelPoints_ant) > 0:
            p0 = rama[0]
            p1 = rama[-1]
            p2 = skelPoints_ant[0]

            dx = p2[0] - p0[0]
            dy = p2[1] - p0[1]
            dist = math.sqrt((dx*dx)+(dy*dy))

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist1 = math.sqrt((dx * dx) + (dy * dy))

            if dist1 < dist:
                invert = True
    elif suma < 0:
        invert = True

    return invert


def is_pose_rara(rama, skelPoints_ant, n_frame):

    pose_rara = False
    skel_length, skel_ant_length, solapamientos = get_solapamiento(rama, skelPoints_ant)
    solapamiento_lenght = len(solapamientos)

    if (skel_length < 56) or (skel_length >= 105): # < 58
        pose_rara = True

    if len(skelPoints_ant) > 0:
        skelPoint_ant_ini = skelPoints_ant[0]
        skelPoint_ant_end = skelPoints_ant[-1]
        dx = (skelPoint_ant_ini[0] - skelPoint_ant_end[0])
        dy = (skelPoint_ant_ini[1] - skelPoint_ant_end[1])
        dist_1 = math.sqrt((dx * dx) + (dy * dy)) # distancia entre extremos de skelPoints_ant

        if len(rama) > 0:
            skelPoint_ini = rama[0]
            skelPoint_end = rama[-1]
            dx = (skelPoint_ini[0] - skelPoint_end[0])
            dy = (skelPoint_ini[1] - skelPoint_end[1])
            dist_2 = math.sqrt((dx * dx) + (dy * dy)) # distancia entre extremos de skelPoints
            min_dist = min(dist_1, dist_2) / 2

            dx = (skelPoint_ant_ini[0] - skelPoint_ini[0])
            dy = (skelPoint_ant_ini[1] - skelPoint_ini[1])
            dist_ini = math.sqrt((dx * dx) + (dy * dy)) # distancia entre ptos iniciales

            dx = (skelPoint_ant_end[0] - skelPoint_end[0])
            dy = (skelPoint_ant_end[1] - skelPoint_end[1])
            dist_end = math.sqrt((dx * dx) + (dy * dy)) # distancia entre ptos finales

            dx = (skelPoint_ant_end[0] - skelPoint_ini[0])
            dy = (skelPoint_ant_end[1] - skelPoint_ini[1])
            dist_ini_competence = math.sqrt((dx * dx) + (dy * dy)) # distancia entre pto final skelPoints_ant y pto inicial skelPoints

            # error posible pérdida del seguimiento de cabeza/cola
            if dist_ini_competence < dist_ini:
                print("Warning in head/tail tracking: dist_ini:", dist_ini, "dist_ini_competence:", dist_ini_competence,
                      "min_dist:", min_dist, "n_frame:", n_frame)
                pose_rara = True

                if (abs(skel_ant_length - skel_length) > (0.2 * skel_ant_length)):

                    if skel_length < skel_ant_length:
                        # Decremento de la longitud al enrrollarse -> probar a introducir fondo en anchuras mayores a 10 en el primer intento
                        print("Warning short skeleton: skel_length:", skel_length, "skel_ant_length:", skel_ant_length,
                              "solapamiento_lenght:", solapamiento_lenght, "dist_ini:", dist_ini, "dist_end:", dist_end,
                              "n_frame:", n_frame)
                    else:
                        # Incremento de longitud al integrar ruido, pueden darse esqueletos sin semtido -> probar a quitar ruido de la img original en el segundo intemto
                        print("Warning long skeleton: skel_length:", skel_length, "skel_ant_length:", skel_ant_length,
                              "solapamiento_lenght:", solapamiento_lenght, "dist_ini:", dist_ini, "dist_end:", dist_end,
                              "n_frame:", n_frame)
        else:
            pose_rara = True

    return pose_rara


def fusiona(rama, skelPoints_ant, shape, red_dist_transform, blue_dist_transform):

    dist_ini = 0
    dist_ini_competence = 0

    if len(skelPoints_ant) > 0:
        skelPoint_ant_ini = skelPoints_ant[0]
        skelPoint_ant_end = skelPoints_ant[-1]
        dx = (skelPoint_ant_ini[0] - skelPoint_ant_end[0])
        dy = (skelPoint_ant_ini[1] - skelPoint_ant_end[1])
        dist_1 = math.sqrt((dx * dx) + (dy * dy))
        min_dist = dist_1 / 2

        if len(rama) > 0:
            skelPoint_ini = rama[0]
            skelPoint_end = rama[-1]
            dx = (skelPoint_ini[0] - skelPoint_end[0])
            dy = (skelPoint_ini[1] - skelPoint_end[1])
            dist_2 = math.sqrt((dx * dx) + (dy * dy))
            min_dist = min(dist_1, dist_2) / 2

            dx = (skelPoint_ant_ini[0] - skelPoint_ini[0])
            dy = (skelPoint_ant_ini[1] - skelPoint_ini[1])
            dist_ini = math.sqrt((dx * dx) + (dy * dy))

            dx = (skelPoint_ant_end[0] - skelPoint_ini[0])
            dy = (skelPoint_ant_end[1] - skelPoint_ini[1])
            dist_ini_competence = math.sqrt((dx * dx) + (dy * dy))

            dx = (skelPoint_ant_end[0] - skelPoint_end[0])
            dy = (skelPoint_ant_end[1] - skelPoint_end[1])
            dist_end = math.sqrt((dx * dx) + (dy * dy))

        #     # error posible pérdida del seguimiento de cabeza/cola
        #     if dist_ini_competence < dist_ini:
        #         rama = skelPoints_ant.copy()
        #         for idx_pto, pto in enumerate(skelPoints_ant):
        #             if (skelPoints_ant[idx_pto][0] < 0) or (skelPoints_ant[idx_pto][0] >= shape[1]) or (
        #                     skelPoints_ant[idx_pto][1] < 0) or (skelPoints_ant[idx_pto][1] >= shape[0]):
        #                 rama.remove(skelPoints_ant[idx_pto])
        #
        else:
            rama = skelPoints_ant.copy()
            for idx_pto, pto in enumerate(skelPoints_ant):
                if (skelPoints_ant[idx_pto][0] < 0) or (skelPoints_ant[idx_pto][0] >= shape[1]) or (
                        skelPoints_ant[idx_pto][1] < 0) or (skelPoints_ant[idx_pto][1] >= shape[0]):
                    rama.remove(skelPoints_ant[idx_pto])

    return rama

def get_skelPoints(skel, gray_recortada, skelPoints_ant, red_dist_transform, blue_dist_transform, intentos):

    endPoints = []
    endPoints_neighs = []
    cruces = []
    cruces_neighs = []
    skelPoints = []
    skelPoints_neighs = []

    h, w = skel.shape
    for x in range(h - 1):
        for y in range(w - 1):
            neighs = neighbours(skel, x, y)
            if (skel[x, y] == 255) and (len(neighs) <= 1):
                endPoints.append((y, x))
                endPoints_neighs.append(neighs)
            elif (skel[x, y] == 255) and (len(neighs) == 2):
                skelPoints.append((y, x))
                skelPoints_neighs.append(neighs)
            elif (skel[x, y] == 255):
                cruces.append((y, x))
                cruces_neighs.append(neighs)
    if len(skelPoints) > 1:
        idx = 0
        if len(skelPoints_ant) > 0:
            skelPoint_ant = skelPoints_ant[0]
            min_dist = 999999
            for index, skelPoint in enumerate(skelPoints):
                dx = (skelPoint_ant[0] - skelPoint[0])
                dy = (skelPoint_ant[1] - skelPoint[1])
                dist_ini = math.sqrt((dx * dx) + (dy * dy))
                if dist_ini < min_dist:
                    min_dist = dist_ini
                    idx = index
        if len(endPoints) == 0:
            print('Warning: the skeleton is a cicle')
            endPoints = [skelPoints[idx]]
            endPoints_neighs = [skelPoints_neighs[idx]]
        else:
            if not skelPoints[idx] in endPoints:
                endPoints.append(skelPoints[idx])
                endPoints_neighs.append(skelPoints_neighs[idx])
    else:
        endPoints = skelPoints
        endPoints_neighs = skelPoints_neighs
    # if len(cruces) == 0:
    #     cruces = endPoints
    #     cruces_neighs = endPoints_neighs
    # else:
    len_cruces_ant = len(cruces)
    if len(cruces) > 0:
        groups, new_cruces, cruces_neighs = simplifica(cruces, cruces_neighs)

        # Actualiza las coordenadas de los nuevos cruces que eran vecinos en skelPoints_neighs y en endPoints_neighs
        for index_group, group in enumerate(groups):
            cruces_coor = []
            for index in group:
                cruces_coor.append(cruces[index])

            skelPoints_neighs = change_coor(skelPoints_neighs, cruces_coor, new_cruces[index_group])
            endPoints_neighs = change_coor(endPoints_neighs, cruces_coor, new_cruces[index_group])

        cruces = new_cruces

        while len(cruces) < len_cruces_ant:
            len_cruces_ant = len(cruces)
            groups, new_cruces, cruces_neighs = simplifica(cruces, cruces_neighs)

            # Actualiza las coordenadas de los nuevos cruces que eran vecinos en skelPoints_neighs y en endPoints_neighs
            for index_group, group in enumerate(groups):
                cruces_coor = []
                for index in group:
                    cruces_coor.append(cruces[index])

                skelPoints_neighs = change_coor(skelPoints_neighs, cruces_coor, new_cruces[index_group])
                endPoints_neighs = change_coor(endPoints_neighs, cruces_coor, new_cruces[index_group])

            cruces = new_cruces

    for endPoint, endPoint_neighs in zip(endPoints, endPoints_neighs):
        cruces.append(endPoint)
        cruces_neighs.append(endPoint_neighs)

    ramas = []
    for index, cruce in enumerate(cruces):
        for cruce_neight in cruces_neighs[index]:
            rama = expande_rama([cruce], [cruce_neight], skelPoints, skelPoints_neighs, cruces, endPoints)
            if not is_in_ramas(rama, ramas):
                if len(skelPoints_ant) > 0:
                    if len(rama) > 0:
                        if invert_rama(rama, skelPoints_ant):
                            rama = rama[::-1]
                ramas.append(rama)

    # # Determina el sentido de los ciclos hacia la zona más oscura
    # for index_r, r in enumerate(ramas):
    #     if len(r) > 0:
    #         p1 = r[0]
    #         p2 = r[-1]
    #         if ((p1[0] == p2[0]) and (p1[1] == p2[1])):
    #             intensity1 = 0
    #             half_interval = int(len(r)/2)
    #             for ind in range(half_interval):
    #                 intensity1 = intensity1 + gray_recortada[r[ind][1], r[ind][0]]
    #             intensity2 = 0
    #             for ind in range(half_interval,len(r)):
    #                 intensity2 = intensity2 + gray_recortada[r[ind][1], r[ind][0]]
    #
    #             if (intensity2 > intensity1):
    #                 ramas[index_r] = r[::-1]
    rama = []
    if len(ramas) == 1:
        rama = ramas[0]
    elif len(ramas) > 1:
        hay_solapamiento = solapan(ramas, skelPoints_ant)
        if hay_solapamiento:
            ramas.sort(reverse=True, key=lambda r: get_solapamiento_lenght(r, skelPoints_ant))
        else:
            ramas.sort(reverse=True, key=get_rama_length)

        rama = ramas.pop(0)
        if len(ramas) < 10:
            cont=0
            rama = concatena_ramas(rama, ramas, skelPoints_ant, red_dist_transform, cont)
            cont=0
        else:
            rama = ramas[0]
    # Mantener el seguimiento de la cabeza/cola, siempre con la misma orientación que la primera rama
    if len(rama) > 0:
        if invert_rama(rama, skelPoints_ant):
            rama = rama[::-1]

    # # Detecta y corrige posibles errores de esqueletización
    # if intentos == 2:
    #     rama = fusiona(rama, skelPoints_ant, skel.shape, red_dist_transform, blue_dist_transform)

    # # reinicio = True
    # if (len(skelPoints_ant) > 0) and (len(rama) > 0):
    #     (x_ini, y_ini) = skelPoints_ant[0]
    #     (x_fin, y_fin) = skelPoints_ant[-1]
    #     (x1_ini, y1_ini) = rama[0]
    #     (x1_fin, y1_fin) = rama[-1]
    #
    #     dx = (x_ini - x1_ini)
    #     dy = (y_ini - y1_ini)
    #     dist_ini = math.sqrt((dx * dx) + (dy * dy))
    #
    #     dx = (x_ini - x1_fin)
    #     dy = (y_ini - y1_fin)
    #     dist_fin = math.sqrt((dx * dx) + (dy * dy))
    #
    #     # if (dist_fin < 19) or (dist_ini < 19):
    #     #     reinicio = False
    #     if dist_fin < dist_ini:
    #         rama = rama[::-1]
    #         #print('Dist seguimiento de cabeza:', dist_fin)
    #     #else:
    #     #    print('Dist seguimiento de cabeza:', dist_ini)

    # if (len(rama) > 0) and (reinicio): # Reinicio el segumineto de cabeza
    #     (x1_ini, y1_ini) = rama[0]
    #     (x1_fin, y1_fin) = rama[-1]
    #
    #     if (red_dist_transform[y1_fin, x1_fin] < 19) or (red_dist_transform[y1_ini, x1_ini] < 19):
    #         if (red_dist_transform[y1_fin, x1_fin] < red_dist_transform[y1_ini, x1_ini]):
    #             rama = rama[::-1]
    #             #print('Red - Dist inicio seguimiento de cabeza:', red_dist_transform[y1_fin, x1_fin])
    #         #else:
    #         #    print('Red - Dist inicio seguimiento de cabeza:', red_dist_transform[y1_ini, x1_ini])
    #
    #     elif (blue_dist_transform[y1_fin, x1_fin] < 19) or (blue_dist_transform[y1_ini, x1_ini] < 19):
    #         if (blue_dist_transform[y1_ini, x1_ini] < blue_dist_transform[y1_fin, x1_fin]):
    #             rama = rama[::-1]
    #             #print('Blue - Dist inicio seguimiento de cabeza:', blue_dist_transform[y1_ini, x1_ini])
    #         #else:
    #         #    print('Blue - Dist inicio seguimiento de cabeza:', blue_dist_transform[y1_fin, x1_fin])
    #
    #     #else:
    #     #    print('*******************Perdida del seguimiento de cabeza')

    # # Si la rama de esqueleto no cumple los criterios se devuelve el esqueleto anterior
    # length_sol = get_rama_length(rama)
    # if (length_sol > 105):
    #     rama = skelPoints_ant.copy()
    #     for idx_pto, pto in enumerate(skelPoints_ant):
    #         if (skelPoints_ant[idx_pto][0] < 0) or (skelPoints_ant[idx_pto][0] >= skel.shape[1]) or (
    #                 skelPoints_ant[idx_pto][1] < 0) or (skelPoints_ant[idx_pto][1] >= skel.shape[0]):
    #             rama.remove(skelPoints_ant[idx_pto])
    return rama

def recalcula_get_dist_egg_skel_ends_min(eggPoint, skelPoints):

    dist_min = 0
    dist1 = 0
    dist2 = 0
    signo = 0
    (cx, cy) = eggPoint
    skel_point = (0, 0)
    vector_egg_skel = (0,0) # vector de origen eggPoint y destino skel_min
    dist_skel_min = 4000
    for x,y in skelPoints:
        dx = (x-cx)
        dy = (y-cy)
        dist_skel = math.sqrt((dx*dx) + (dy*dy))
        if dist_skel < dist_skel_min:
            dist_skel_min = dist_skel
            x_min = x
            y_min = y

    if (dist_skel_min < 6):
    #if dist_skel_min < 4000:
        skel_point = (x_min, y_min)
        index = find_index(skel_point, skelPoints)
        dist1 = get_rama_length(skelPoints[0:index+1])
        dist2 = get_rama_length(skelPoints[index:len(skelPoints)])
        dist_min = min(dist1, dist2)

        idx = index-int(index/4)
        signo = np.sign((y_min - skelPoints[idx][1]) * (cx - skelPoints[idx][0]) - (x_min - skelPoints[idx][0]) * (cy - skelPoints[idx][1]))

        dx = y_min-cy
        dy = x_min-cx
        if dist_skel_min == 0:
            vector_egg_skel = (dx, dy)
        else:
            vector_egg_skel = (dx/dist_skel_min, dy/dist_skel_min)

    return dist_min, dist1, dist2, signo, vector_egg_skel, skel_point


def get_dist_egg_skel_ends_min(eggPoint, skelPoints):

    dist_min = 0
    dist1 = 0
    dist2 = 0
    signo = 0
    (cx, cy) = eggPoint
    vector_egg_skel = (0,0) # vector de origen eggPoint y destino skel_min
    dist_skel_min = 4000
    for x,y in skelPoints:
        dx = (x-cx)
        dy = (y-cy)
        dist_skel = math.sqrt((dx*dx) + (dy*dy))
        if dist_skel < dist_skel_min:
            dist_skel_min = dist_skel
            x_min = x
            y_min = y

    if dist_skel_min < 4000:
        index = find_index((x_min, y_min), skelPoints)
        dist1 = get_rama_length(skelPoints[0:index+1])
        dist2 = get_rama_length(skelPoints[index:len(skelPoints)])
        dist_min = min(dist1, dist2)

        idx = index-int(index/4)
        signo = np.sign((y_min - skelPoints[idx][1]) * (cx - skelPoints[idx][0]) - (x_min - skelPoints[idx][0]) * (cy - skelPoints[idx][1]))

        dx = y_min-cy
        dy = x_min-cx
        if dist_skel_min == 0:
            vector_egg_skel = (dx, dy)
        else:
            vector_egg_skel = (dx/dist_skel_min, dy/dist_skel_min)

        new_point = (cx - dy, cy - dx)
        #try:
        #    if cx - dy>4024:
        #        new_point[0]=4024
        #    if cx - dy<0:
        #        new_point[0]=0
        #    if cy - dx>3036:
        #        new_point[1]=3036
        #    if cy - dx<0:
        #        new_point[1]=0
        dist_min_c, dist1_c, dist2_c, signo_c, vector_egg_skel_c, (x_min_c, y_min_c) = recalcula_get_dist_egg_skel_ends_min(new_point, skelPoints)

        if dist_min_c > dist_min:

            dx = y_min - y_min_c
            dy = x_min - x_min_c
            dist_med = math.sqrt((dx * dx) + (dy * dy))/2.0

            holgura = dist_med - dist_skel_min

            if holgura < 2:
                dist_min = dist_min_c
                dist1 = dist1_c
                dist2 = dist2_c
                signo = signo_c
                vector_egg_skel = vector_egg_skel_c

    return dist_min, dist1+dist2, signo, vector_egg_skel

# def get_dist_skel_egg_max(egg_point, skel, egg_dilated):
#     (cx, cy) = egg_point
#     dist_skel_min = 4000
#     pts_skel = np.where(skel == 255)
#     for x,y in zip(pts_skel[1],pts_skel[0]):
#         dx = (x-cx)
#         dy = (y-cy)
#         dist_skel = math.sqrt((dx*dx) + (dy*dy))
#         if dist_skel < dist_skel_min:
#             dist_skel_min = dist_skel
#             x_min = x
#             y_min = y
#
#     dist_skel_egg_max = 0
#     if dist_skel_min < 4000:
#         pts_egg = np.where(egg_dilated == 255)
#         for x,y in zip(pts_egg[1],pts_egg[0]):
#             dx = (x - x_min)
#             dy = (y - y_min)
#             dist_skel_egg = math.sqrt((dx * dx) + (dy * dy))
#             if dist_skel_egg > dist_skel_egg_max:
#                 dist_skel_egg_max = dist_skel_egg
#
#     return dist_skel_egg_max

# def get_dist_skel_egg_max(skel_dist_transform, egg_dilated):
#
#     pts_egg = np.where(egg_dilated == 255)
#     dist_skel_egg_max = max(skel_dist_transform[pts_egg])
#
#     return dist_skel_egg_max


def  get_sum_diff(diff_recortada, cx, cy):
    #values = []
    sum_diff = 0
    cont = 0
    for offsset_x in range(-1, 2):
        cx_act = cx + offsset_x
        if (cx_act >= 0) and (cx_act < diff_recortada.shape[1]):
            for offsset_y in range(-1, 2):
                cy_act = cy+offsset_y
                if (cy_act >= 0) and (cy_act < diff_recortada.shape[0]):
                    sum_diff = sum_diff + diff_recortada[cy_act, cx_act]
                    cont = cont + 1
                    #values.append(diff_recortada[cy_act, cx_act])

    if cont > 0:
        sum_diff = sum_diff / cont

    #median_diff = statistics.median(values)

    return sum_diff


def chi(aux, x, y):
    chi_val = 0
    val_ant = aux[x,y-1]
    for off in [[-1,-1],[-1,0],[-1,1],[0,1],[1,1],[1,0],[1,-1],[0,-1]]:
        val_act = aux [x+off[0],y+off[1]]
        if not val_ant == val_act:
            chi_val = chi_val + 1
        val_ant == val_act

    return chi_val


def connecting_holes_of_one_pixel(eggs):
    h, w = eggs.shape
    aux = eggs.copy()
    for x in range(1, h - 1):
        for y in range(1, w - 1):
            if aux[x, y] == 0:
                if chi(aux, x, y) == 4:
                    eggs[x, y] = 255
    return eggs


def gradiente(img, pixel):
    grad = 0
    (cy, cx) = pixel

    if (cy > 0) and (cy < img.shape[0]-2) and (cx > 0) and (cx < img.shape[1]-2):
        gx = (img[cy-1, cx-1] + (2 * img[cy-1, cx]) + img[cy-1, cx+1]) - (img[cy+1, cx-1] + (2 * img[cy+1, cx]) + img[cy+1, cx+1])
        gy = (img[cy-1, cx-1] + (2 * img[cy, cx-1]) + img[cy+1, cx-1]) - (img[cy-1, cx+1] + (2 * img[cy, cx+1]) + img[cy+1, cx+1])
        grad = math.sqrt((gx*gx)+(gy*gy))

        #grad = (4*img[cy, cx]) - img[cy-1, cx] - img[cy+1, cx] - img[cy, cx-1] - img[cy, cx+1]

    return grad


def eroding_isolated_pixels(blue):
    h, w = blue.shape
    aux = blue.copy()
    for x in range(1, h - 1):
        for y in range(1, w - 1):
            val_neigh = 0
            for off in [[-1, -1], [-1, 0], [-1, 1], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1]]:
                if aux[x + off[0], y + off[1]] == 255:
                    val_neigh += 1
            if (aux[x, y] == 255):
                if (val_neigh <= 2):
                    blue[x, y] = 0

    return blue


def is_frame_egg_laying(path, name_video, img_res, eggs_dist_transform_recortada, gray_recortada, n_frame, diff_recortada, skelPoints_ant, intentos):

    is_frame_egg_laying = False
    features = []

    # Red channel contains pixels with positive motion which are potential egg points
    eggs = img_res[:, :, 2]
    ret, eggs = cv2.threshold(eggs, 254, 255, cv2.THRESH_BINARY)
    height, width = eggs.shape[0:2]
    red_dist_transform = cv2.distanceTransform(255-eggs, cv2.DIST_L2, 3)

    # Connecting holes of one pixel
    # eggs = connecting_holes_of_one_pixel(eggs)

    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5), (3, 3))
    # eggs = cv2.dilate(eggs, kernel, iterations=1)

    # cv2.imshow("eggs", eggs)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # cv2.imshow("red_dist_transform", (red_dist_transform*255/np.max(red_dist_transform)).astype(np.uint8))
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    #
    # cv2.imshow("eggs_dist_transform_recortada", (eggs_dist_transform_recortada*255/np.max(eggs_dist_transform_recortada)).astype(np.uint8))
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # Blue channel contains pixels with negative motion
    blue = img_res[:, :, 0]
    #blue = eroding_isolated_pixels(blue)
    blue_neg = 255 - blue
    blue_dist_transform = cv2.distanceTransform(blue_neg, cv2.DIST_L2, 3)

    # Green channel contains the first skelPoints
    skel = img_res[:,:,1]
    first_skelPoints = np.where(skel == 255)

    # Select the skelPoints which represents the worm
    if np.count_nonzero(skel) == 0:
        print("La imagen es completamente negra.")
    skelPoints = get_skelPoints(skel, gray_recortada, skelPoints_ant, red_dist_transform, blue_dist_transform, intentos)
    skel[first_skelPoints] = 0
    skelPoints_x = [x[0] for x in skelPoints]
    skelPoints_y = [x[1] for x in skelPoints]
    if len(skelPoints_x) > 0:
        skel[(np.array(skelPoints_y), np.array(skelPoints_x))] = 255
        img_res[skelPoints_y[0], skelPoints_x[0]] = (250, 255, 250)  # Marca la cabeza/cola del gusano

    skel_neg = 255 - skel
    skel_dist_transform = cv2.distanceTransform(skel_neg, cv2.DIST_L2, 3)

    # endPoints = [skelPoints[0], skelPoints[-1]]
    #print('endPoints:', endPoints) # Asagurar que son 2
    # Marca la cabeza/cola del gusano del skelPoints_ant
    if len(skelPoints_ant) > 0:
        if (skelPoints_ant[0][1] >= 0) and (skelPoints_ant[0][1] < img_res.shape[0]) and (skelPoints_ant[0][0] >= 0) and (skelPoints_ant[0][0] < img_res.shape[1]):
            if img_res[skelPoints_ant[0][1], skelPoints_ant[0][0], 1] == 255:
                img_res[skelPoints_ant[0][1], skelPoints_ant[0][0]] = (250, 255, 250)
            else:
                img_res[skelPoints_ant[0][1], skelPoints_ant[0][0]] = (250, 250, 250)

    # cv2.imshow("img_res", img_res)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # For each potential egg
    #_, contours, hierarchy = cv2.findContours(eggs, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours_eggs, hierarchy = cv2.findContours(eggs, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for contour_egg in contours_eggs:

        # Se evita que al dilatar se unan dos huevos potenciales
        egg_dilated = np.zeros((height, width), np.uint8)
        cv2.drawContours(egg_dilated, [contour_egg], -1, 255, thickness=cv2.FILLED)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5), (3, 3))
        egg_dilated = cv2.dilate(egg_dilated, kernel)

        contours, hierarchy = cv2.findContours(egg_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            M = cv2.moments(contour)
            area = M['m00']
            # if area == 0:
            #     area = 1
            #print('area egg:', area)

            #if ((area > 5) and (area < 90)):
            if ((area > 18) and (area < 90)):

                # _, (w_egg, h_egg),_ = cv2.minAreaRect(contour)
                # if w_egg >= h_egg:
                #     ma1 = w_egg
                #     MA1 = h_egg
                # else:
                #     ma1 = h_egg
                #     MA1 = w_egg
                #
                # ratio1 = MA1/ma1

                (x, y), (MA, ma), angle = cv2.fitEllipse(contour)
                ratio = MA/ma
                #print('MA:', MA, 'ma:', ma, 'ratio:', ratio)

                #if ((area <= 52) and (ratio > 0.65)) or ((area > 52) and (ratio > 0.56)):
                #if ((area <= 50) and (ratio > 0.54)) or ((area > 50) and (ratio > 0.3)):
                if ratio > 0.5:

                    cx = int((M['m10'] / area) + 0.5)
                    cy = int((M['m01'] / area) + 0.5)
                    if cy>4024:
                        cy=4024
                    if cy<0:
                        cy=0
                    if cx>3036:
                        cx=3036
                    if cx<0:
                        cx=0

                    #print('eggs_dist_transform_recortada[', cy,',', cx, '] =', eggs_dist_transform_recortada[cy,cx])
                    #cv2.imshow("eggs_dist_transform_recortada", eggs_dist_transform_recortada)
                    #cv2.waitKey(0)
                    #cv2.destroyAllWindows()

                    # eggs_dist_transform_recortada marca distancias con las diferencias entre la primera y la última imagen del vídeo
                    if eggs_dist_transform_recortada[cy,cx] == 0:

                        grad = gradiente(gray_recortada, (cy, cx))

                        #egg_dilated = np.zeros((height, width), np.uint8)
                        #cv2.drawContours(egg_dilated, [contour], -1, 255, thickness=cv2.FILLED)
                        pts_egg = np.where(egg_dilated == 255)

                        dist_skel_egg = max(skel_dist_transform[pts_egg])
                        #print('dist_skel_egg:', dist_skel_egg)

                        if (dist_skel_egg > 6) and (dist_skel_egg < 12.4):

                            dist_min, skel_lenght, signo, vector_egg_skel = get_dist_egg_skel_ends_min((cx,cy), skelPoints)
                            ratio_dist_min_skel_lenght = dist_min/(skel_lenght+1)
                            #print('dist_min:', dist_min, 'skel_lenght:', skel_lenght, 'ratio_skel_lenght_dist_min:', ratio_dist_min_skel_lenght)

                            #if (dist_min > 20) and (dist_min < 4000):
                            #if (dist_min > 26) and (dist_min < 4000):
                            #if ((skel_lenght < 55) and (ratio_dist_min_skel_lenght > 0.1)) or ( (skel_lenght >= 55) and (ratio_dist_min_skel_lenght > 0.35) ):
                            if ratio_dist_min_skel_lenght > 0.32:

                                # if abs(vector_egg_skel[1]) > 0:
                                #     v_normal = (-vector_egg_skel[1], vector_egg_skel[0])
                                # else:
                                #     v_normal = (vector_egg_skel[1], -vector_egg_skel[0])
                                #
                                # rect_blue_mask = np.zeros(blue_dist_transform.shape, dtype=np.uint8)
                                # d0 = (2.5 * v_normal[0], 2.5 * v_normal[1])
                                # d1 = (5.5*v_normal[0], 5.5*v_normal[1])
                                # d2 = (5.5*vector_egg_skel[0], 5.5*vector_egg_skel[1])
                                # pts = np.array([[cx + d0[1], cy + d0[0]],
                                #                 [cx - d0[1], cy - d0[0]],
                                #                 [cx - d1[1] + d2[1], cy - d1[0] + d2[0]],
                                #                 [cx + d1[1] + d2[1], cy + d1[0] + d2[0]]], np.int32)
                                # rect_blue_mask = cv2.fillPoly(rect_blue_mask, [pts], 255)
                                #
                                # # img_res_copy = img_res.copy()
                                # # img_res_copy = cv2.fillPoly(img_res_copy, [pts], (255,255,255))
                                # # cv2.imwrite("/home/antonio/Descargas/egg_laying_new_v2/img_res_ant.bmp", img_res)
                                # # cv2.imwrite("/home/antonio/Descargas/egg_laying_new_v2/img_res_pos.bmp", img_res_copy)
                                #
                                # blue_act = blue.copy()
                                # # blue_neg_1 = 255 - cv2.bitwise_and(blue_act, blue_act, mask=rect_blue_mask)
                                # # blue_dist_transform_1 = cv2.distanceTransform(blue_neg_1, cv2.DIST_L2, 3)
                                # blue_neg_2 = 255 - cv2.bitwise_and(blue_act, blue_act, mask=255 - rect_blue_mask)
                                # blue_dist_transform_2 = cv2.distanceTransform(blue_neg_2, cv2.DIST_L2, 3)
                                #
                                # #blue_dist_min_1 = blue_dist_transform_1[cy, cx]
                                # blue_dist_min = blue_dist_transform_2[cy, cx]

                                blue_dist_min = blue_dist_transform[cy, cx]
                                #print('blue_dist_min:', blue_dist_min)

                                if (blue_dist_min < 5) or (blue_dist_min > 7.8): # > 10
                                #if blue_dist_min > 7.8: # > 10

                                    # sum_diff = sum(diff_recortada[pts_egg])/len(pts_egg[0])
                                    sum_diff = get_sum_diff(diff_recortada, cx, cy)
                                    #print('sum_diff:', sum_diff)

                                    if (sum_diff > 21) or ((sum_diff > 9) and (dist_skel_egg > 6.4) and (ratio_dist_min_skel_lenght > 0.38) and (ratio > 0.7)):

                                        ratio_grad = grad / (sum_diff + 0.1)

                                        if ratio_grad < 13.1:

                                            if (area > 21) and (ratio > 0.6) and (dist_skel_egg > 7) and (dist_skel_egg < 12.4) and (ratio_dist_min_skel_lenght > 0.38) and (blue_dist_min > 10.5) and (sum_diff > 21) and (ratio_grad < 13.1):
                                                e_incertidumbre = 1
                                            else:
                                                e_incertidumbre = 0

                                            trozos_path = path.split('/')
                                            total_name = ''
                                            for idx_trozo in range(5, len(trozos_path)-1):
                                                total_name = total_name + trozos_path[idx_trozo] + '/'
                                            total_name = total_name + name_video

                                            #print('area:', area, 'ratio:', ratio, 'eggs_dist_transform_recortada[', cy,',', cx, '] =', eggs_dist_transform_recortada[cy,cx], 'dist_skel_egg:', dist_skel_egg, 'dist_min:', dist_min, 'skel_lenght:', skel_lenght)
                                            print(total_name, n_frame, e_incertidumbre, 'lado:', signo, 'area:', area, 'ratio:', ratio, 'dist_skel_egg:', dist_skel_egg, 'skel_lenght:', skel_lenght, 'ratio_skel_lenght_dist_min:', ratio_dist_min_skel_lenght, 'blue_dist:', blue_dist_min,'sum_diff:', sum_diff, 'grad:', grad, 'ratio_grad:', ratio_grad)

                                            features.append([n_frame, cy, cx, area, ratio, dist_skel_egg, skel_lenght, ratio_dist_min_skel_lenght, blue_dist_min, sum_diff, e_incertidumbre])
                                            img_res[cy,cx] = (128, 128, 255) # Marca el pixel centroide del huevo
                                            is_frame_egg_laying = True

    return is_frame_egg_laying, skelPoints, img_res, features


def get_changes_red(path, name_video, cap, ini_frame, end_frame):
    cap.set(cv2.CAP_PROP_POS_FRAMES, end_frame)
    ret, img_end = cap.read()
    gray = cv2.cvtColor(img_end, cv2.COLOR_BGR2GRAY)
    noise_end = get_noise(gray)
    #cv2.imwrite("/home/antonio/Descargas/egg_laying_new_v3/noise_end.bmp", noise_end)
    gray_end = borra_gusanos(path, name_video, img_end)

    cap.set(cv2.CAP_PROP_POS_FRAMES, ini_frame)
    ret, img = cap.read()
    if ret == False:
        img = img_end
    # cv2.imshow("img", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    gray_ant = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    noise_ini = get_noise(gray_ant)
    #cv2.imwrite("/home/antonio/Descargas/egg_laying_new_v3/noise_ini.bmp", noise_ini)

    noise = cv2.bitwise_and(noise_end, noise_end, mask=noise_ini)
    # Cierra los agujeros internos del ruido para evitar ciclos del esqueleto
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10), (3, 3))
    noise = cv2.morphologyEx(noise, cv2.MORPH_CLOSE, kernel)
    #cv2.imwrite("/home/antonio/Descargas/egg_laying_v4/completos/6/000004_imgs/noise_and.bmp", noise)

    # img_changes = np.zeros((gray.shape[0], gray.shape[1], 3), np.uint8)
    img_changes_red = np.zeros((gray.shape[0], gray.shape[1]), np.uint8)
    eggs_dist_transform = np.full((gray.shape[0], gray.shape[1]), 9999999.0)

    #poses = []

    diff = gray_ant.astype(int) - gray.astype(int)
    #pts_diff = np.where(diff >= 30)
    #pts_diff = np.where(diff >= 27) # v5
    pts_diff = np.where(diff >= 23)  # v6
    #pts_diff_neg = np.where(diff <= -20)

    if len(pts_diff[0]) > 0:
        # img_changes[pts_diff] = (0, 0, 255)
        # img_changes[pts_diff_neg] = (255, 0, 0)
        img_changes_red[pts_diff] = 255

        #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21), (3, 3))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (27, 27), (3, 3))
        img_changes_red = cv2.dilate(img_changes_red, kernel, iterations=1)

        img_neg = 255 - img_changes_red
        eggs_dist_transform = cv2.distanceTransform(img_neg, cv2.DIST_L2, 3)

        #cv2.imshow("dist_transform", dist_transform)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

    return eggs_dist_transform, img_changes_red, noise, gray_end


def dilate(bw, iterations, value):
    value_fondo = 255 - value
    h, w = bw.shape
    res = bw.copy()
    for t in range(iterations):
        for x in range(h-2):
            x = x + 1
            for y in range(w-2):
                y = y + 1
                if bw[x,y] == value_fondo:
                    #print(bw[x-1, y-1], bw[x-1, y])
                    #print(bw[x, y], bw[x, y-1])
                    if ( (bw[x-1,y-1] == value_fondo) and (bw[x-1, y] == value) and (bw[x, y-1] == value) ):
                        res[x,y] = value

                    #print(bw[x-1, y], bw[x-1, y+1])
                    #print(bw[x, y], bw[x, y+1])
                    if ( (bw[x-1, y] == value) and (bw[x-1, y+1] == value_fondo) and (bw[x, y+1] == value) ):
                        res[x,y] = value
        bw = res.copy()
    return res


def process(path, cap, ini_frame, end_frame, eggs_dist_transform):

    cont_eggs = 0

    #print('Process from:', str(ini_frame),'to:', str(end_frame))
    cap.set(cv2.CAP_PROP_POS_FRAMES, end_frame)
    ret, img = cap.read()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    cap.set(cv2.CAP_PROP_POS_FRAMES, ini_frame)
    ret, img = cap.read()
    # cv2.imshow("img", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    gray_ant = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #img_changes = np.zeros((gray.shape[0], gray.shape[1], 3), np.uint8)
    img_changes_red = np.zeros((gray.shape[0], gray.shape[1]), np.uint8)
    #img_changes_blue = np.zeros((gray.shape[0], gray.shape[1]), np.uint8)

    diff = gray_ant.astype(int) - gray.astype(int)
    #pts_diff = np.where(diff >= 30)
    pts_diff = np.where(diff >= 23) # v6
    #pts_diff_neg = np.where(diff <= -20)

    min_worm_dist_to_eggs = 0
    


    if len(pts_diff[0]) > 0:
        #img_changes[pts_diff] = (0, 0, 255)
        #img_changes[pts_diff_neg] = (255, 0, 0)
        img_changes_red[pts_diff] = 255

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5), (3, 3))
        img_changes_red = cv2.dilate(img_changes_red, kernel, iterations=1)

        #img_changes_red = img_changes[:, :, 2]
        #_, contours, hierarchy = cv2.findContours(img_changes_red, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours, hierarchy = cv2.findContours(img_changes_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contour_max = np.asarray([])
        area_max = 0
        for contour in contours:
            M = cv2.moments(contour)
            area = M['m00']

            # Se detecta el gusano como el contorno de área máxima
            if area > area_max:
                area_max = area
                contour_max = contour
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                if cy>4024:
                    cy=4024
                if cy<0:
                    cy=0
                if cx>3036:
                    cx=3036
                if cx<0:
                    cx=0

            #if (area <= 5) or (area >= 57*3):
                # cv2.drawContours(img_changes_red, [contour], -1, 0, thickness=cv2.FILLED)
                #cv2.drawContours(img_changes, [contour], -1, (0, 0, 0), thickness=cv2.FILLED)
            #else:
            if (area > 5) and (area < 57*3):
                # (x, y), (MA, ma), angle = cv2.fitEllipse(contour)
                # ratio = MA / ma
                # if ((area <= 52) and (ratio > 0.65)) or ((area > 52) and (ratio > 0.56)):
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                if cy>4024:
                    cy=4024
                if cy<0:
                    cy=0
                if cx>3036:
                    cx=3036
                if cx<0:
                    cx=0
                #cv2.imshow("eggs_dist_transform", eggs_dist_transform)
                #cv2.waitKey(0)
                #cv2.destroyAllWindows()

                if eggs_dist_transform[cy, cx] == 0:
                    cont_eggs = cont_eggs + 1

        # distancia mínima entre los candidatos a huevos y el centroide del gusano en el último frame
        if (contour_max.size > 0):
            # Posición del gusano en el último frame
            M = cv2.moments(contour_max)
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            if cy>4024:
                cy=4024
            if cy<0:
                cy=0
            if cx>3036:
                cx=3036
            if cx<0:
                cx=0
            min_worm_dist_to_eggs = eggs_dist_transform[cy, cx]
        #print('min_worm_dist_to_eggs:', min_worm_dist_to_eggs)

        #cv2.imshow(str(ini_frame)+':'+str(end_frame), img_changes)
        #print('Waiting! Press key...')
        #cv2.waitKey(0)
        #cv2.imwrite(path + "img_changes_20.bmp", img_changes)
        #cv2.destroyAllWindows()

    if (cont_eggs == 0) and (min_worm_dist_to_eggs > 21) or not hay_celegan:
        frame_items = []
        #print('Frames:', ini_frame, end_frame, 'eggs:', frame_items, 'min_worm_dist_to_eggs:', min_worm_dist_to_eggs)
    elif ((end_frame - ini_frame) <= 1124):
        frame_items = process_in_detail(path, cap, ini_frame, end_frame, eggs_dist_transform)
        #print('Frames:', ini_frame, end_frame, 'eggs:', frame_items, 'min_worm_dist_to_eggs:', min_worm_dist_to_eggs)
    else:
        med_frame = ini_frame + int((end_frame - ini_frame)/2)
        frame_items = process(path, cap, ini_frame, med_frame, eggs_dist_transform)
        fram_items2 = process(path, cap, med_frame, end_frame, eggs_dist_transform)
        for frame_item in fram_items2:
            frame_items.append(frame_item)

    return frame_items


def match_item_tracked_eggs(item, tracked_eggs):

    item_frame = item[0]
    item_x = item[1]
    item_y = item[2]

    for tracked_egg in tracked_eggs:
        #keys_egg = list(tracked_egg.keys())
        for key_egg in tracked_egg.keys():
        #if len(keys_egg) > 0:
            #key_egg = keys_egg[0]
            e_frame = tracked_egg[key_egg][0]

            if e_frame > item_frame:
                e_x = key_egg[1]
                e_y = key_egg[0]

                dx = e_x-item_x
                dy = e_y-item_y
                dist = math.sqrt((dx * dx) + (dy * dy))

                if dist < 11.8:
                    predicted_frames = tracked_egg[key_egg][2]
                    print("Match", item_frame, e_frame, "with", dist, ". Is", item_frame, "in", predicted_frames, "?")
                    return True, tracked_egg, key_egg

    return False, None, None


def get_frames(skeleton_points_for_checking, points_min):

    est_frames = []

    for point_min in points_min:
        act_frames = skeleton_points_for_checking[point_min]
        for frame in act_frames:
            if not frame in est_frames:
                est_frames.append(frame)

    return est_frames


def process_in_detail(path, name_video, cap, ini_frame, end_frame, eggs_dist_transform, img_changes_0, noise, gray_end, init_pose, show = False, simplify = False):

    #frame_items_ini = []
    #eggs_tracked = []
    frame_items = []
    skelPoints_ant = []

    img_result_tracking = np.zeros((eggs_dist_transform.shape[0], eggs_dist_transform.shape[1], 3), np.uint8)
    img_result_tracking_blue = np.zeros((eggs_dist_transform.shape[0], eggs_dist_transform.shape[1]), np.uint8)
    img_result_tracking_green = np.zeros((eggs_dist_transform.shape[0], eggs_dist_transform.shape[1]), np.uint8)
    #img_tracked = np.zeros((eggs_dist_transform.shape[0], eggs_dist_transform.shape[1], 3), np.uint8)
    #pts_eggs = np.where(eggs_dist_transform == 0)
    #img_result[pts_eggs] = (0,0,255)

    # anchura_max_ant = 0
    # beta = 0.05
    # cont = 0
    #
    # skel_lenght_ant = 0
    # beta1 = 0.05
    cont1 = 0

    skel_lenght_media = 0

    #cx_ant = int(eggs_dist_transform.shape[0]/2)
    #cy_ant = int(eggs_dist_transform.shape[1]/2)
    cx_ant = init_pose[0]
    cy_ant = init_pose[1]
    worm_detected = False
    tracked_eggs = []
    tracked_egg = {} # {egg: [n_frame, contador, est_frames, e_incertidumbre], egg: [n_frame, contador, est_frames, e_incertidumbre]}
    skeleton_points_for_checking = {}

    if simplify or show:
        path = path.replace('egg_laying', 'egg_laying_new')
        fps = cap.get(cv2.CAP_PROP_FPS)
        shape = (128, 128)
        poses = []

    #backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=43, detectShadows=False)

    #cont_track = 0
    n_frame = ini_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, n_frame)
    path_name_video = os.path.join(path, name_video)
    if not os.path.exists(path_name_video + "_imgs"):
        os.makedirs(path_name_video + "_imgs")

    while (n_frame <= end_frame) and (cap.isOpened()):
        print(path, '--------------------------n_frame: ', n_frame)
        ret, img = cap.read()
        if ret == False:
            gray = np.ones((int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))), np.uint8)*255
            path_name_video = os.path.join(path, name_video)
            cv2.imwrite(path_name_video + "_imgs/gray_ini_sin_gusanos.bmp", gray)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(path_name_video + '.mp4', fourcc, fps, shape)
            break
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        #if n_frame == 2966: #todo comentar
        #    print('n_frame:', n_frame) #todo comentar

        if n_frame == ini_frame:
            gray_ini = borra_gusanos(path, name_video, img)
            path_name_video = os.path.join(path, name_video)
            cv2.imwrite(path_name_video + "_imgs/gray_ini_sin_gusanos.bmp", gray_ini)
            img_result_tracking_green = 255 - gray  # ini_frame -> channel green (1)

            #gray_ini = gray.copy()
            #img_result_tracking[:, :, 1] = 255 - gray_ini # ini_frame -> channel green (1)
            gray_ant = gray.copy()
            if simplify:
                #cv2.imwrite(path+ name_video + "_ini.bmp", gray)
                # Crea videos nuevos
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                #out = cv2.VideoWriter(path_name_video + '.mp4', fourcc, fps, shape, 0)
                out = cv2.VideoWriter(path_name_video + '.mp4', fourcc, fps, shape)

        # if simplify and (n_frame == end_frame):
        #     cv2.imwrite(path_name_video + "_end.bmp", gray)

        diff = gray_ant.astype(int) - gray.astype(int)
        #max_diff = np.max(diff)
        #pts_diff = np.where(diff >= 30)
        pts_diff = np.where(diff >= 23)  # v2
        if len(pts_diff[0]) > 0:
            suficient_skel_lenght = False
            intentos = 1
            anchura_max_act = 4.7
            while (not suficient_skel_lenght) and (intentos <= 2):
            #while (not suficient_skel_lenght) and (intentos <= 1):

                # # # todo : probar a quitar el ruido antes de erosionar los grises en el segundo intento
                # if intentos == 2:
                #     img_copy = img.copy()
                #     ptos_noise = np.where(noise == 255)
                #     img_copy[ptos_noise] = (255,255,255)
                #     img_seg_dilated, img_seg, boxes = get_segmentation(img_copy, pts_diff, intentos)
                #     img_res = cv2.bitwise_and(img_copy, img_copy, mask=img_seg_dilated)
                # else:
                img_seg_dilated, img_seg, boxes = get_segmentation(img, pts_diff, intentos, worm_detected)
                img_res = cv2.bitwise_and(img, img, mask=img_seg_dilated)

                if (intentos == 1) and (show == True):
                    img_result = np.zeros(img_res.shape, np.uint8)
                    img_result[:, :, 0] = img_changes_0
                    img_result[:, :, 1] = 255 - gray
                    img_result[:, :, 2] = 255 - gray_ant
                    img_result = cv2.putText(img_result, 'frame: ' + str(n_frame), org, font, fontScale, color, thickness, cv2.LINE_AA)

                    #cv2.imwrite(path_name_video + "_imgs/" + str(n_frame) + "_ori.bmp", gray)
                    #cv2.imwrite(path_name_video + "_imgs/" + str(n_frame) + "_seg.bmp", img_seg)

                # Si hay varios boxes se selecciona el box más cercano al anterior
                if worm_detected:
                    dist_min_ini = 199 # (Debe ser mayor a 99)
                else:
                    dist_min_ini = 9999999
                dist_min = dist_min_ini
                for box in boxes:
                    x_ini_act = box[0, 1]  # y
                    y_ini_act = box[0, 0]  # x
                    x_fin_act = box[1, 1]  # y+h
                    y_fin_act = box[2, 0]  # x+w

                    cx_act = x_ini_act + int((x_fin_act - x_ini_act) / 2)
                    cy_act = y_ini_act + int((y_fin_act - y_ini_act) / 2)

                    dx = cx_act - cx_ant
                    dy = cy_act - cy_ant
                    dist_recorrida = math.sqrt((dx * dx) + (dy * dy))

                    if dist_recorrida < dist_min:
                        dist_min = dist_recorrida
                        cx = cx_act
                        cy = cy_act
                        x_ini = x_ini_act  # y
                        y_ini = y_ini_act  # x
                        x_fin = x_fin_act  # y+h
                        y_fin = y_fin_act  # x+w

                if (len(boxes) > 0) and (dist_min < 199 or dist_min_ini == 9999999):

                    # Recorte de imágenes según box
                    diff_recortada = diff[x_ini:x_fin, y_ini:y_fin]

                    #pts_diff_recortada = np.where(diff_recortada >= 30)
                    pts_diff_recortada = np.where(diff_recortada >= 23)  # v2
                    if len(pts_diff_recortada[0]) > 0:

                        # print(len(pts_diff_recortada[0]))

                        eggs_dist_transform_recortada = eggs_dist_transform[x_ini:x_fin, y_ini:y_fin]
                        img_res_recortada = img_res[x_ini:x_fin, y_ini:y_fin]
                        # Marca en los movimientos positivos en rojo sobre img_res_recortada
                        img_res_recortada[pts_diff_recortada] = (0, 0, 255)

                        #pts_diff_neg_recortada = np.where(diff_recortada <= -30)
                        pts_diff_neg_recortada = np.where(diff_recortada <= -23) # v2
                        # Marca en los movimientos negativos en azul sobre img_res_recortada
                        img_res_recortada[pts_diff_neg_recortada] = (255, 0, 0)

                        cantidad_movimiento = (len(pts_diff_recortada[0]), len(pts_diff_neg_recortada[0]))

                        skelPoints_ant_copy = skelPoints_ant.copy()
                        deleted = 0
                        for idx_pto, pto in enumerate(skelPoints_ant_copy):
                            skelPoints_ant_copy[idx_pto] = (skelPoints_ant_copy[idx_pto][0] - y_ini, skelPoints_ant_copy[idx_pto][1] - x_ini)
                            if (skelPoints_ant_copy[idx_pto][1] >= 0) and (skelPoints_ant_copy[idx_pto][1] < img_res_recortada.shape[0]) and (skelPoints_ant_copy[idx_pto][0] >= 0) and (skelPoints_ant_copy[idx_pto][0] < img_res_recortada.shape[1]):
                                # Marca el esqueleto anterior en verde oscuro sobre img_res_recortada
                                img_res_recortada[skelPoints_ant_copy[idx_pto][1], skelPoints_ant_copy[idx_pto][0]] = (0,128,0)
                                skelPoints_ant[idx_pto - deleted] = skelPoints_ant_copy[idx_pto]
                            else:
                                del skelPoints_ant[idx_pto-deleted]
                                deleted += 1

                        img_seg_recortada = img_seg[x_ini:x_fin, y_ini:y_fin]

                        # Abrir segmentación en las zonas demasiado anchas
                        res_dist_transform = cv2.distanceTransform(img_seg_recortada, cv2.DIST_L2, 3)
                        anchura_max_act = max(res_dist_transform[np.where(res_dist_transform > 0)])
                        if anchura_max_act >= 7:
                            pts_anchos = np.where(res_dist_transform >= anchura_max_act)
                        else:
                            pts_anchos = np.where(res_dist_transform >= 7)

                        # Actualiza anchura_max
                        # anchura_max = ((1- beta) * anchura_max_act) + (beta * anchura_max_ant)
                        # anchura_max_ant = anchura_max
                        # anchura_max = anchura_max / (1-beta**(cont+1))
                        # cont = cont + 1
                        # error_anchura_max = anchura_max - anchura_max_act

                        if len(pts_anchos[0]) > 0:
                            min_dist_ancho = 999999
                            for point_ancho in zip(pts_anchos[1], pts_anchos[0]):
                                for skel_point_ant in skelPoints_ant:
                                    dx = point_ancho[0] - skel_point_ant[0]
                                    dy = point_ancho[1] - skel_point_ant[1]
                                    dist = math.sqrt((dx * dx) + (dy * dy))
                                    if dist < min_dist_ancho:
                                        min_dist_ancho = dist

                            #if min_dist_ancho > 3:
                            if min_dist_ancho > 1.5:
                                if intentos == 1:
                                    pts_anchos = np.where(res_dist_transform >= 7)
                                    if anchura_max_act >= 8:
                                        pts_anchos = np.where(res_dist_transform >= anchura_max_act - 2)
                                elif intentos == 2:
                                    # # get_segmentation -> kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                                    # pts_anchos = np.where(res_dist_transform >= 8)
                                    # if anchura_max_act >= 9:
                                    #     pts_anchos = np.where(res_dist_transform >= anchura_max_act - 2)

                                    # # get_segmentation -> kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                                    # pts_anchos = np.where(res_dist_transform >= 10)
                                    # if anchura_max_act >= 11:
                                    #     pts_anchos = np.where(res_dist_transform >= anchura_max_act - 2)

                                    # # get_segmentation -> kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)
                                    # pts_anchos = np.where(res_dist_transform >= 12)
                                    # if anchura_max_act >= 13:
                                    #     pts_anchos = np.where(res_dist_transform >= anchura_max_act - 2)

                                    # get_segmentation -> kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)
                                    pts_anchos = np.where(res_dist_transform >= 14)
                                    if anchura_max_act >= 15:
                                        pts_anchos = np.where(res_dist_transform >= anchura_max_act - 2)

                                img_seg_recortada[pts_anchos] = 0
                                img_seg_recortada = dilate(img_seg_recortada, 1, 0)

                        # Añade los pixeles de ruido tras cierre, para evitar bucles producidos por el ruido en la operación de esqueletización
                        noise_recortada = noise[x_ini:x_fin, y_ini:y_fin]
                        ptos_noise = np.where(noise_recortada == 255)
                        img_seg_recortada[ptos_noise] = 255

                        #cv2.imwrite(path + "imgs/" + str(n_frame) + "_noise.bmp", noise_recortada)
                        #cv2.imwrite(path + "imgs/" + str(n_frame) + "_seg.bmp", img_seg_recortada)
                        #cv2.imwrite(path + "imgs/" + str(n_frame) + "_ori.bmp", img[x_ini:x_fin, y_ini:y_fin])

                        # # Marca el esqueleto del gusano en verde sobre img_res_recortada
                        skel = skeletonize(img_seg_recortada, method='lee')
                        h_img, w_img = img_res_recortada.shape[:2]
                        h_skel, w_skel = skel.shape[:2]

                        if h_skel > h_img or w_skel > w_img:
                            skel = skel[:h_img, :w_img]

                        img_res_recortada[skel == 255] = (0, 255, 0)
                        #cv2.imwrite(path + "imgs/" + str(n_frame) + "_skel.bmp", img_res_recortada)

                        is_frame_egg_laying_flag, skelPoints, img_res_recortada, features = is_frame_egg_laying(path, name_video, img_res_recortada, eggs_dist_transform_recortada, gray[x_ini:x_fin, y_ini:y_fin], n_frame, diff_recortada, skelPoints_ant, intentos)


                        # # Marca la zona segmentada del gusano en el canal azul de img_res_recortada
                        # for x1 in range(img_res_recortada.shape[0]):
                        #     for y1 in range(img_res_recortada.shape[1]):
                        #         if img_seg_recortada[x1, y1] == 255:
                        #             img_res_recortada[x1, y1, 0] = 255

                        # if intentos == 1:
                        #     diff_ini = gray_ini[x_ini:x_fin, y_ini:y_fin].astype(int) - gray[x_ini:x_fin, y_ini:y_fin].astype(int)
                        #     if is_frame_egg_laying_flag and (cont_track == 0):
                        #         cont_track = 1
                        #     if cont_track > 0:
                        #         img_diff_ini = np.zeros((x_fin-x_ini, y_fin-y_ini), np.uint8)
                        #         pts_diff = np.where(diff_ini >= 23)
                        #         img_diff_ini[pts_diff] = 255
                        #         img_diff_ini = img_diff_ini - noise_recortada
                        #         _, contours, hierarchy = cv2.findContours(img_diff_ini, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                        #         for contour in contours:
                        #             area = cv2.contourArea(contour)
                        #             rect = cv2.boundingRect(contour)
                        #             print('Tracking:', n_frame, area)
                        #
                        #         cv2.imwrite(path_name_video + "_imgs/" + name_video + "_" + str(n_frame) + "_diff_ini.bmp",
                        #                     img_diff_ini)
                        #
                        #         if cont_track < 50:
                        #             cont_track += 1
                        #         else:
                        #             cont_track = 0

                        # Pasar a coordenadas globales
                        for idx_pto, pto in enumerate(skelPoints):
                            skelPoints[idx_pto] = (y_ini + skelPoints[idx_pto][0], x_ini + skelPoints[idx_pto][1])

                        for idx_pto, pto in enumerate(skelPoints_ant):
                            skelPoints_ant[idx_pto] = (y_ini + skelPoints_ant[idx_pto][0], x_ini + skelPoints_ant[idx_pto][1])

                        # Actualiza skel_lenght
                        skel_lenght_act = get_rama_length(skelPoints)
                        # Segmenta los huevos
                        if (intentos == 1) and (n_frame % 10 == 0):

                            # Actualización de los puntos de centrales del esqueleto como huevos potenciales asociandolos a los frames
                            new_points_for_checking = []
                            ini = int(len(skelPoints)/5)
                            for idx in range(ini, ini*4):
                                new_points_for_checking.append(skelPoints[idx])

                            for new_point_for_checking in new_points_for_checking:
                                if new_point_for_checking in skeleton_points_for_checking.keys():
                                    if skeleton_points_for_checking[new_point_for_checking] == None:
                                        skeleton_points_for_checking[new_point_for_checking] = [n_frame]
                                    else:
                                        skeleton_points_for_checking[new_point_for_checking].append(n_frame)
                                else:
                                    skeleton_points_for_checking[new_point_for_checking] = [n_frame]

                            # Actualización de los puntos seleccionados para chequear huevos potenciales cercanos
                            selected_points = []
                            skeleton_points_for_checking_copy = skeleton_points_for_checking.copy()
                            for key_skel in skeleton_points_for_checking_copy.keys():
                                min_dist = 9999999
                                if len(skelPoints) > 0:
                                    cuarto = int(len(skelPoints)/4)
                                    for skel_point in [skelPoints[0], skelPoints[cuarto], skelPoints[2*cuarto], skelPoints[3*cuarto], skelPoints[-1]]:
                                        dx = key_skel[0] - skel_point[0]
                                        dy = key_skel[1] - skel_point[1]
                                        dist = math.sqrt((dx * dx) + (dy * dy))
                                        if dist < min_dist:
                                            min_dist = dist
                                            key_skel_min = key_skel

                                if min_dist >= 100:
                                    if key_skel_min in skeleton_points_for_checking.keys():
                                        del skeleton_points_for_checking[key_skel_min]
                                elif min_dist > 15:
                                    selected_points.append(key_skel_min)
                            # if n_frame == 800 or n_frame == 5030 or n_frame == 5540 or n_frame == 14150 or n_frame == 14100:
                            #
                            #     res_egg = np.zeros((gray.shape[0], gray.shape[1], 3), np.uint8)
                            #     res_egg[:, :, 2] = 255 - gray
                            #
                            #     selected_points_x = [x[0] for x in selected_points]
                            #     selected_points_y = [x[1] for x in selected_points]
                            #
                            #     if len(selected_points_y) > 0:
                            #         selected_points_img = np.zeros((gray.shape[0], gray.shape[1]), np.uint8)
                            #         selected_points_img[(np.array(selected_points_y), np.array(selected_points_x))] = 255
                            #         res_egg[:, :, 1] = selected_points_img
                            #
                            #     checking_points_x = []
                            #     checking_points_y = []
                            #     for key_skel in skeleton_points_for_checking.keys():
                            #         checking_points_x.append(key_skel[0])
                            #         checking_points_y.append(key_skel[1])
                            #
                            #     checking_points_img = np.zeros((gray.shape[0], gray.shape[1]), np.uint8)
                            #     checking_points_img[(np.array(checking_points_y), np.array(checking_points_x))] = 255
                            #
                            #     skelPoints_x = [x[0] for x in skelPoints]
                            #     skelPoints_y = [x[1] for x in skelPoints]
                            #     checking_points_img[(np.array(skelPoints_y), np.array(skelPoints_x))] = 255
                            #
                            #     res_egg[:, :, 0] = checking_points_img
                            #
                            #     cv2.imwrite(path_name_video + "_imgs/" + name_video + "_" + str(n_frame) + "_points.bmp", res_egg)

                            #img_eggs = backSub.apply(gray)
                            #background = backSub.getBackgroundImage()
                            #cv2.imwrite(path_name_video + "_imgs/" + str(n_frame) + "_background.bmp", background)

                            diff_gray = cv2.subtract(gray_ini, gray)
                            #img_eggs = cv2.inRange(diff_gray, 43, 255)  # Rango de valores de huevos seguros
                            img_eggs = cv2.inRange(diff_gray, 30, 255)  # Segmentación de huevos

                            # img_eggs = cv2.subtract(img_seg, noise)
                            # cv2.imwrite(path_name_video + "_imgs/" + str(n_frame) + "_noise.bmp", noise)
                            # cv2.imwrite(path_name_video + "_imgs/" + str(n_frame) + "_eggs.bmp", img_eggs)
                            #
                            #
                            # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5), (3, 3))
                            # eggs_dilated = cv2.dilate(img_eggs, kernel)
                            # cv2.imwrite(path_name_video + "_imgs/" + str(n_frame) + "_eggs_dilated.bmp", eggs_dilated)

                            contours, hierarchy = cv2.findContours(img_eggs, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                            # cv2.imwrite(path_name_video + "_imgs/" + str(n_frame) + "_seg.bmp", img_seg)

                            # if n_frame >= 2111:
                            #     selected_points_x = [x[0] for x in selected_points]
                            #     selected_points_y = [x[1] for x in selected_points]
                            #
                            #     res_egg = np.zeros((img_eggs.shape[0], img_eggs.shape[1], 3), np.uint8)
                            #     res_egg[:, :, 1] = 255 - gray_ini
                            #     res_egg[:, :, 2] = 255 - gray
                            #
                            #     cx_egg = 3368
                            #     cy_egg = 1957
                            #     cv2.circle(img_eggs, (cx_egg, cy_egg), 15, 255, 1)
                            #     img_eggs[(np.array(selected_points_y), np.array(selected_points_x))] = 128
                            #     res_egg[:, :, 0] = img_eggs
                            #
                            #     cv2.imwrite(path_name_video + "_imgs/" + name_video + "_" + str(n_frame) + "_" + str(
                            #         cy_egg) + "x" + str(cx_egg) + "_eggs.bmp", res_egg)

                            tracked_eggs_copy = tracked_eggs.copy()
                            for cnt_id, contour in enumerate(contours):
                                M = cv2.moments(contour)
                                area = M['m00']
                                # if area == 0:
                                #     area = 1
                                # if n_frame > 6810:
                                #     print('area egg:', area)

                                if (area > 0.9) and (area < 39): # area > 2.0,  3.5

                                    rect = cv2.minAreaRect(contour)
                                    if rect[1][0] >= rect[1][1]:
                                        elongacion = rect[1][1] / rect[1][0]
                                    else:
                                        elongacion = rect[1][0] / rect[1][1]

                                    if elongacion >= 0.3: # 0.39 # 0.44

                                        cx_egg = int((M['m10'] / area) + 0.5)
                                        cy_egg = int((M['m01'] / area) + 0.5)
                                        egg = (cx_egg, cy_egg)

                                        dx = cx_act - cy_egg
                                        dy = cy_act - cx_egg
                                        dist = math.sqrt((dx * dx) + (dy * dy))

                                        if dist < 200: # todo: probar a reducir esta distancia, dist inicial 200

                                            # Calculo de ratio_egg
                                            img_egg = np.zeros((img_eggs.shape[0], img_eggs.shape[1]), np.uint8)
                                            cv2.drawContours(img_egg, [contour], -1, 255, thickness=cv2.FILLED)

                                            (x, y, w, h) = cv2.boundingRect(contour)
                                            x = max(0, x - 2)
                                            y = max(0, y - 2)
                                            yh = min(img_eggs.shape[0] - 1, y + h + 2)
                                            xw = min(img_eggs.shape[1] - 1, x + w + 2)
                                            img_egg = img_egg[y:yh, x:xw]

                                            diff_gray_recortada = diff_gray[y:yh, x:xw]
                                            ptos_egg = np.where(img_egg == 255)
                                            max_diff = max(diff_gray_recortada[ptos_egg])

                                            gray_recortada = gray[y:yh, x:xw]
                                            min_gray = min(gray_recortada[ptos_egg])

                                            ratio_diff_gray = max_diff / (min_gray + 0.5)

                                            if ratio_diff_gray > 0.35:

                                                img_egg_dist_transform = cv2.distanceTransform(img_egg, cv2.DIST_L2, 3)
                                                anchura_max_egg = max(
                                                    img_egg_dist_transform[np.where(img_egg_dist_transform > 0)])

                                                skel_egg = skeletonize(img_egg, method='lee')
                                                length_skel_egg = len(np.where(skel_egg == 255)[0])

                                                ratio_egg = area / (anchura_max_egg * length_skel_egg)

                                                # if n_frame == 800 or n_frame == 5030 or n_frame == 5540 or n_frame == 14150 or n_frame == 14100:
                                                #     print(n_frame, 'area egg:', area, 'anchura_max_egg:', anchura_max_egg,
                                                #           'length_skel_egg:', length_skel_egg, 'ratio_egg:', ratio_egg, 'elongacion:', elongacion)

                                                if ratio_egg > 0.34: #1.5, 0.99

                                                    dist_min_egg_skel = 9999999
                                                    points_min = []
                                                    for point in selected_points:
                                                        dx = point[0] - cx_egg
                                                        dy = point[1] - cy_egg
                                                        dist = math.sqrt((dx * dx) + (dy * dy))

                                                        if dist < 10:
                                                            points_min.append(point)
                                                            if dist < dist_min_egg_skel:
                                                                dist_min_egg_skel = dist
                                                                point_min = point

                                                    if dist_min_egg_skel < 4: #10

                                                        if (area >= 3.5) and (area < 25) and (elongacion > 0.45) and (ratio_egg > 0.85) and (dist_min_egg_skel < 3) and (ratio_diff_gray > 0.4):
                                                            e_incertidumbre = 1
                                                        else:
                                                            e_incertidumbre = 0

                                                        # Tracking eggs
                                                        dist_min_eggs = 9
                                                        for idx_eggs, tracked_egg in enumerate(tracked_eggs_copy):
                                                            for key_egg in tracked_egg.keys():
                                                                dx = key_egg[0] - egg[0]
                                                                dy = key_egg[1] - egg[1]
                                                                dist = math.sqrt((dx * dx) + (dy * dy))

                                                                if dist < dist_min_eggs:
                                                                    dist_min_eggs = dist
                                                                    idx_eggs_min = idx_eggs

                                                        if dist_min_eggs < 9:
                                                            if dist_min_eggs == 0:
                                                                tracked_eggs[idx_eggs_min][egg][1] = tracked_eggs[idx_eggs_min][egg][1] + 1
                                                            else:
                                                                est_frames = get_frames(skeleton_points_for_checking, points_min)
                                                                #tracked_eggs[idx_eggs_min][egg] = [n_frame, 1, skeleton_points_for_checking[point_min], e_incertidumbre]
                                                                tracked_eggs[idx_eggs_min][egg] = [n_frame, 1, est_frames, e_incertidumbre]

                                                                selected_points_x = [x[0] for x in selected_points]
                                                                selected_points_y = [x[1] for x in selected_points]

                                                                y1_ini = max(0, cy_egg - 128)
                                                                y1_fin = min(img_eggs.shape[0], cy_egg + 128)
                                                                x1_ini = max(0, cx_egg - 128)
                                                                x1_fin = min(img_eggs.shape[1], cx_egg + 128)

                                                                res_egg = np.zeros((y1_fin - y1_ini, x1_fin - x1_ini, 3), np.uint8)
                                                                res_egg[:, :, 1] = 255 - gray_ini[y1_ini:y1_fin, x1_ini:x1_fin]
                                                                res_egg[:, :, 2] = 255 - gray[y1_ini:y1_fin, x1_ini:x1_fin]

                                                                cv2.circle(img_eggs, (cx_egg, cy_egg), 15, 255, 1)
                                                                # img_eggs[(np.array(selected_points_y), np.array(selected_points_x))] = 255 - img_eggs[(np.array(selected_points_y), np.array(selected_points_x))]
                                                                img_eggs[(np.array(selected_points_y), np.array(selected_points_x))] = 128
                                                                res_egg[:, :, 0] = img_eggs[y1_ini:y1_fin, x1_ini:x1_fin]

                                                                cv2.imwrite(path_name_video + "_imgs/" + name_video + "_" + str(n_frame) + "_" + str(cy_egg) + "x" + str(cx_egg) + "_" + str(cnt_id) + "_eggs.bmp", res_egg)

                                                        else:
                                                            trozos_path = path.split('/')
                                                            total_name = ''
                                                            for idx_trozo in range(5, len(trozos_path)-1):
                                                                total_name = total_name + trozos_path[idx_trozo] + '/'
                                                            total_name = total_name + name_video
                                                            print(total_name, n_frame, e_incertidumbre, "new egg:", egg, 'area egg:', area, 'anchura_max_egg:', anchura_max_egg,
                                                                  'length_skel_egg:', length_skel_egg, 'ratio_egg:', ratio_egg,
                                                                  'elongacion:', elongacion, 'max_diff:', max_diff, 'min_gray:', min_gray, 'ratio_diff_gray:', ratio_diff_gray, 'frames:', skeleton_points_for_checking[point_min])

                                                            est_frames = get_frames(skeleton_points_for_checking, points_min)
                                                            #tracked_eggs.append({egg: [n_frame, 1, skeleton_points_for_checking[point_min], e_incertidumbre]})
                                                            tracked_eggs.append({egg: [n_frame, 1, est_frames, e_incertidumbre]})
                                                            #print(n_frame, "new egg:", egg, "area:", area)

                                                            selected_points_x = [x[0] for x in selected_points]
                                                            selected_points_y = [x[1] for x in selected_points]

                                                            y1_ini = max(0, cy_egg - 128)
                                                            y1_fin = min(img_eggs.shape[0], cy_egg + 128)
                                                            x1_ini = max(0, cx_egg - 128)
                                                            x1_fin = min(img_eggs.shape[1], cx_egg + 128)

                                                            res_egg = np.zeros((y1_fin-y1_ini, x1_fin-x1_ini, 3), np.uint8)
                                                            res_egg[:, :, 1] = 255 - gray_ini[y1_ini:y1_fin, x1_ini:x1_fin]
                                                            res_egg[:, :, 2] = 255 - gray[y1_ini:y1_fin, x1_ini:x1_fin]

                                                            cv2.circle(img_eggs, (cx_egg, cy_egg), 15, 255, 1)
                                                            #img_eggs[(np.array(selected_points_y), np.array(selected_points_x))] = 255 - img_eggs[(np.array(selected_points_y), np.array(selected_points_x))]
                                                            img_eggs[(np.array(selected_points_y), np.array(selected_points_x))] = 128
                                                            res_egg[:, :, 0] = img_eggs[y1_ini:y1_fin, x1_ini:x1_fin]

                                                            cv2.imwrite(path_name_video + "_imgs/" + name_video + "_" + str(n_frame) + "_" + str(cy_egg) + "x" + str(cx_egg) + "_" + str(cnt_id) + "_eggs.bmp", res_egg)

                                                            # gray_copy = gray.copy()
                                                            # cv2.circle(gray_copy, (cx_egg, cy_egg), 15, 255, 1)
                                                            # gray_copy[(np.array(selected_points_y), np.array(selected_points_x))] = 255 - gray_copy[(np.array(selected_points_y),np.array(selected_points_x))]
                                                            # cv2.imwrite(path_name_video + "_imgs/" + name_video + "_" + str(n_frame) + "_" + str(cy_egg) + "x" + str(cx_egg) + "_" + str(cnt_id) + "_gray.bmp", gray_copy[cy_egg-128:cy_egg+128, cx_egg-128:cx_egg+128])

                                                            # skelPoints_x = [x[0] for x in skelPoints]
                                                            # skelPoints_y = [x[1] for x in skelPoints]
                                                            #
                                                            # gray_copy = gray.copy()
                                                            # cv2.circle(gray_copy, (cx_egg, cy_egg), 15, 255, 1)
                                                            # gray_copy[(np.array(skelPoints_y), np.array(skelPoints_x))] = 255 - gray_copy[(np.array(skelPoints_y),np.array(skelPoints_x))]
                                                            # cv2.imwrite(path_name_video + "_imgs/" + name_video + "_" + str(n_frame) + "_" + str(cy_egg) + "x" + str(cx_egg) + "_" + str(cnt_id) + "_gray.bmp", gray_copy[cy_egg-128:cy_egg+128, cx_egg-128:cx_egg+128])
                                                            #
                                                            # cv2.circle(img_eggs, (cx_egg, cy_egg), 15, 255, 1)
                                                            # img_eggs[(np.array(skelPoints_y), np.array(skelPoints_x))] = 255 - img_eggs[(np.array(skelPoints_y), np.array(skelPoints_x))]
                                                            # cv2.imwrite(path_name_video + "_imgs/" + name_video + "_" + str(n_frame) + "_" + str(cy_egg) + "x" + str(cx_egg) + "_" + str(cnt_id) + "_eggs.bmp", img_eggs[cy_egg-128:cy_egg+128, cx_egg-128:cx_egg+128])


                            # print("tracked_eggs:", tracked_eggs)

                            # if n_frame >= 6810:
                            #
                            #     skelPoints_x = [x[0] for x in skelPoints]
                            #     skelPoints_y = [x[1] for x in skelPoints]
                            #
                            #     # cv2.circle(img_eggs, (2222, 2212), 15, 255, 1)
                            #     # img_eggs[(np.array(skelPoints_y), np.array(skelPoints_x))] = 255 - img_eggs[(np.array(skelPoints_y), np.array(skelPoints_x))]
                            #     # cv2.imwrite(path_name_video + "_imgs/" + str(n_frame) + "_diff_background.bmp", img_eggs)
                            #
                            #     gray_copy = gray.copy()
                            #     cv2.circle(gray_copy, (2212, 2144), 15, 255, 1)
                            #     gray_copy[(np.array(skelPoints_y), np.array(skelPoints_x))] = 255 - gray_copy[(np.array(skelPoints_y), np.array(skelPoints_x))]
                            #     cv2.imwrite(path_name_video + "_imgs/" + str(n_frame) + "_gray.bmp", gray_copy)

                        # Hay tres posibles formas de salir:
                        # 1.- se consigue una longitud de esqueleto adecuada en el primer intento
                        # 2.- se consigue una longitud de esqueleto adecuada en el segundo intento
                        # 3.- 0 posición rara, debido a que no se alcanza la longitud del esqueleta adecuada en el segundo intento o se tiene una anchura incorrecta en el primer intento
                        # Guardar poses raras
                        if (intentos == 2) and (is_pose_rara(skelPoints, skelPoints_ant, n_frame) or (anchura_max_act < 2) or (anchura_max_act > 10)):
                            #print(n_frame, 'pose_rara', skel_lenght_act, anchura_max_act)
                            cv2.imwrite(path_name_video + "_rare_poses/" + str(n_frame) + '_' + str(int(skel_lenght_act)) + '_' + str(int(anchura_max_act)) + ".bmp", img_res_recortada)
                            #skelPoints_ant = [] # pierdo el seguimiento de la cabeza/cola

                            if worm_detected:
                                # Actualiza la trayectoria en la imagen de resultados
                                #cv2.line(img_result_tracking_blue, (cy_ant, cx_ant), (cy, cx), 255, thickness=2)

                                if len(skelPoints) >= 5:
                                    central_skelPoints = []
                                    ini = int(len(skelPoints) / 5)
                                    for idx in range(ini * 2, ini * 3):
                                        central_skelPoints.append(skelPoints[idx])

                                    skelPoints_x = [x[0] for x in central_skelPoints]
                                    skelPoints_y = [x[1] for x in central_skelPoints]
                                    img_result_tracking_blue[(np.array(skelPoints_y), np.array(skelPoints_x))] = 255

                                cx_ant = cx
                                cy_ant = cy
                                skelPoints_ant = skelPoints.copy()
                        elif skel_lenght_act >= 56: # 58
                            # skel_lenght = ((1 - beta1) * skel_lenght_act) + (beta1 * skel_lenght_ant)
                            # skel_lenght_ant = skel_lenght
                            # skel_lenght = skel_lenght / (1-beta1**(cont1 + 1))
                            skel_lenght_media = ((skel_lenght_media * cont1) + skel_lenght_act) / (cont1 + 1)
                            cont1 = cont1 + 1

                            # Finalizar los intentos
                            suficient_skel_lenght = True

                            if worm_detected:
                                # Actualiza la trayectoria en la imagen de resultados
                                #cv2.line(img_result_tracking_blue, (cy_ant, cx_ant), (cy, cx), 255, thickness=2)

                                if len(skelPoints) >= 5:
                                    central_skelPoints = []
                                    ini = int(len(skelPoints) / 5)
                                    for idx in range(ini * 2, ini * 3):
                                        central_skelPoints.append(skelPoints[idx])

                                    skelPoints_x = [x[0] for x in central_skelPoints]
                                    skelPoints_y = [x[1] for x in central_skelPoints]
                                    img_result_tracking_blue[(np.array(skelPoints_y), np.array(skelPoints_x))] = 255

                            else:
                                # Empezar a dibujar la trayectoria en la imagen de resultados
                                worm_detected = True

                            cx_ant = cx
                            cy_ant = cy
                            skelPoints_ant = skelPoints.copy()

                            if is_frame_egg_laying_flag and cantidad_movimiento[1] < 43:
                                #print(n_frame, 'skel_lenght', skel_lenght, 'anchura_max:', anchura_max)
                                print("cantidad_movimiento:", cantidad_movimiento, "skel_lenght_media:", skel_lenght_media)

                                # Coordenadas del centroide del huevo respecto a la imagen original
                                for ind in range(len(features)):
                                    features[ind][1] = x_ini + features[ind][1]
                                    features[ind][2] = y_ini + features[ind][2]
                                    #dist_skel_egg = features[ind][5]
                                    #print('dist_skel_egg - anchura_max:', dist_skel_egg - anchura_max)

                                    cv2.imwrite(path_name_video + "_imgs/" + name_video + "_" + str(n_frame) + "_" + str(features[ind][1]) + "x" + str(features[ind][2]) + ".bmp", img_res_recortada)

                                # frame_items_ini.append(n_frame)
                                #frame_items_ini.append((features, gray_ant, img_res_recortada))
                                #eggs_tracked.append((1, 1))
                                frame_items.append(features)
                                # e_x = features[0][1]
                                # e_y = features[0][2]
                                # img_result_tracking_blue = cv2.circle(img_result_tracking_blue, (e_y, e_x), 15, 128, -1)
                                # img_result_tracking_blue = cv2.putText(img_result_tracking_blue, str(n_frame), (e_y + 15, e_x + 15),
                                #                                   font, 0.25, 255, 1, cv2.LINE_AA)

                                # cv2.imshow('img_res_recortada', img_res_recortada)
                                # print('Waiting! Press key...')
                                # if cv2.waitKey(0) & 0xFF == ord('q'):
                                #    break
                if (intentos == 1) and (show == True):
                    cv2.imwrite(path_name_video + "_imgs/img_result.bmp", img_result)
                    #input()

                    #cv2.imshow('img_result', img_result)
                    #print('Waiting! Press key...')
                    #if cv2.waitKey(0) & 0xFF == ord('q'):
                    #    break

                intentos = intentos + 1


        if simplify:
            if out.isOpened():
                cx_ini = max(0, cx_ant - int(shape[0] / 2))
                cy_ini = max(0, cy_ant - int(shape[1] / 2))
                if cy_ini+shape[1]>4024:
                    cy_ini=4023-shape[1]
                    worm_detected=False
                if cy_ini<0:
                    cy_ini=0
                    worm_detected=False
                if cx_ini+shape[0]>3036:
                    cx_ini=3035-shape[0]
                    worm_detected=False
                if cx_ini<0:
                    cx_ini=0
                    worm_detected=False
                #out.write(gray[cx_ini:cx_ini + shape[0], cy_ini:cy_ini + shape[1]])
                frame_video = np.zeros((shape[0], shape[1], 3), np.uint8)
                frame_video[:, :, 0] = 255 - gray_end[cx_ini:cx_ini + shape[0], cy_ini:cy_ini + shape[1]]
                frame_video[:, :, 1] = 255 - gray_ant[cx_ini:cx_ini + shape[0], cy_ini:cy_ini + shape[1]]
                frame_video[:, :, 2] = 255 - gray[cx_ini:cx_ini + shape[0], cy_ini:cy_ini + shape[1]]
                #cv2.imwrite(path_name_video + "frame_video.bmp", frame_video)
                out.write(frame_video)
            else:
                print('Error no se puede crear el vídeo 1...')
                break

            poses.append((cx_ant, cy_ant))


        n_frame = n_frame + 1
        gray_ant = gray.copy()

    #if show == True:
    #    cv2.destroyAllWindows()

    # Actualiza la imagen de resultados
    img_result_tracking_red = 255 - gray.copy() # end_frame -> channel red

    # Filtra tracked_eggs dependiendo de la cantidad de frames en las que ha habido tracking
    final_tracked_eggs = tracked_eggs.copy()
    deleted_tracked_eggs = 0
    for idx_eggs, tracked_egg in enumerate(tracked_eggs):
        tracked_frames = 0
        tracked_egg_keys = list(tracked_egg.keys())
        if len(tracked_egg_keys) > 0:
            key_egg_ini = tracked_egg_keys[0]
            for key_egg in tracked_egg_keys:
                tracked_frames += tracked_eggs[idx_eggs][key_egg][1]

            if tracked_frames <= 3:
                print(tracked_eggs[idx_eggs][key_egg_ini][0], "deleted egg:", key_egg_ini, "tracked_frames:", tracked_frames)
                del final_tracked_eggs[idx_eggs - deleted_tracked_eggs]
                deleted_tracked_eggs += 1
            else:
                print(tracked_eggs[idx_eggs][key_egg_ini][0], "new egg:", key_egg_ini, "tracked_frames:", tracked_frames)

    track_eggs_frames = []
    # Marca final_tracked_eggs si la incertidumbre es 1
    for idx_eggs, tracked_egg in enumerate(final_tracked_eggs):
        tracked_egg_keys = list(tracked_egg.keys())
        if len(tracked_egg_keys) > 0:
            key_egg_ini = tracked_egg_keys[0]
            e_incertidumbre = tracked_egg[key_egg_ini][3]
            if e_incertidumbre == 1:
                e_x = key_egg_ini[0]
                e_y = key_egg_ini[1]
                e_frame = tracked_egg[key_egg_ini][0]
                cv2.circle(img_result_tracking_red, (e_x, e_y), 10, 255, 1)
                alpha = random.uniform(-math.pi/2, math.pi/2)
                cv2.putText(img_result_tracking_red, str(e_frame), (e_x + int(15*math.cos(alpha) + 0.5), e_y + int(15*math.sin(alpha) + 0.5)),
                                                       font, 0.25, 255, 1, cv2.LINE_AA)
            track_eggs_frames.append(tracked_egg[key_egg_ini][0])

    ok_eggs_frames = []
    nok_eggs_frames = []
    # Empareja frame_items con final_tracked_eggs y marca los diferentes casos
    for items in frame_items:
        for item in items:
            e_incertidumbre = item[10]
            if e_incertidumbre == 1:
                match, tracked_egg, key_egg = match_item_tracked_eggs(item, final_tracked_eggs)
                if match:
                    e_incertidumbre = tracked_egg[key_egg][3]
                    if e_incertidumbre != 1:
                        e_x = key_egg[0]
                        e_y = key_egg[1]
                        e_frame = tracked_egg[key_egg][0]
                        cv2.circle(img_result_tracking_red, (e_x, e_y), 10, 128, 1)
                        alpha = random.uniform(-math.pi / 2, math.pi / 2)
                        cv2.putText(img_result_tracking_red, str(e_frame),
                                    (e_x + int(15 * math.cos(alpha) + 0.5), e_y + int(15 * math.sin(alpha) + 0.5)),
                                    font, 0.25, 128, 1, cv2.LINE_AA)

                    ok_eggs_frames.append([item[0], tracked_egg[key_egg][0]])
                else:
                    ok_eggs_frames.append([item[0], 0])

                e_x = item[1]
                e_y = item[2]
                cv2.circle(img_result_tracking_green, (e_y, e_x), 10, 255, 1)
                alpha = random.uniform(-math.pi / 2, math.pi / 2)
                cv2.putText(img_result_tracking_green, str(item[0]),
                            (e_y + int(15 * math.cos(alpha) + 0.5), e_x + int(15 * math.sin(alpha) + 0.5)),
                            font, 0.25, 255, 1, cv2.LINE_AA)

            else:
                match, tracked_egg, key_egg = match_item_tracked_eggs(item, final_tracked_eggs)
                if match:
                    e_incertidumbre = tracked_egg[key_egg][3]
                    if e_incertidumbre != 1:
                        e_x = key_egg[0]
                        e_y = key_egg[1]
                        e_frame = tracked_egg[key_egg][0]
                        cv2.circle(img_result_tracking_red, (e_x, e_y), 10, 128, 1)
                        alpha = random.uniform(-math.pi/2, math.pi/2)
                        cv2.putText(img_result_tracking_red, str(e_frame), (e_x + int(15*math.cos(alpha) + 0.5), e_y + int(15*math.sin(alpha) + 0.5)),
                                                               font, 0.25, 128, 1, cv2.LINE_AA)

                    e_x = item[1]
                    e_y = item[2]
                    cv2.circle(img_result_tracking_green, (e_y, e_x), 10, 128, 1)
                    alpha = random.uniform(-math.pi/2, math.pi/2)
                    cv2.putText(img_result_tracking_green, str(item[0]), (e_y + int(15*math.cos(alpha) + 0.5), e_x + int(15*math.sin(alpha) + 0.5)),
                                                           font, 0.25, 128, 1, cv2.LINE_AA)

                    ok_eggs_frames.append([item[0], tracked_egg[key_egg][0]])

                else:
                    nok_eggs_frames.append(item[0])

    img_result_tracking[:, :, 0] = img_result_tracking_blue
    img_result_tracking[:, :, 1] = img_result_tracking_green
    img_result_tracking[:, :, 2] = img_result_tracking_red
    cv2.imwrite(path_name_video + "_img_result_tracking.bmp", img_result_tracking)

    if simplify:
        np.save(path_name_video + '_poses.npy', poses)
        np.save(path_name_video + '_track_eggs_frames.npy', track_eggs_frames)
        np.save(path_name_video + '_ok_eggs_frames.npy', ok_eggs_frames)
        np.save(path_name_video + '_nok_eggs_frames.npy', nok_eggs_frames)
        out.release()

    #print('frame_items:', frame_items)
    return frame_items


def simplify_video(path, name_video, shape):

    path_out = path.replace('egg_laying', 'egg_laying_new')
    path_out_name_video = os.path.join(path_out, name_video)

    path_name_video = os.path.join(path, name_video)
    cap = cv2.VideoCapture(path_name_video + '.mp4')

    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps:", fps)

    totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print("totalNoFrames:", totalNoFrames)

    durationInSeconds = totalNoFrames / fps
    print("durationInSeconds:", durationInSeconds, "s")

    # anchura_max_ant = 4.7
    # beta = 0.05
    # cont = 0

    ini_frame = 0
    end_frame = int(totalNoFrames) - 1

    n_frame = ini_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, n_frame)

    cx_ant = 0
    cy_ant = 0
    poses = []
    while (n_frame <= end_frame) and (cap.isOpened()):
        ret, img = cap.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if n_frame == ini_frame:
            gray_ant = gray.copy()

            cv2.imwrite(path_out_name_video + "_ini.bmp", gray)

            # Crea videos nuevos
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(path_out_name_video + '.mp4', fourcc, fps, shape, 0)

        # if n_frame == end_frame:
        #     cv2.imwrite(path_out_name_video + "_end.bmp", gray)

        diff = gray_ant.astype(int) - gray.astype(int)
        #pts_diff = np.where(diff >= 30)
        #pts_diff = np.where(diff >= 27)  # v5
        pts_diff = np.where(diff >= 23)  # v6

        img_seg_dilated, img_seg, boxes = get_segmentation(img, pts_diff, 1, True)
        #img_res = cv2.bitwise_and(img, img, mask=img_seg_dilated)
        #img_res = cv2.putText(img_res, 'frame: ' + str(n_frame), org, font, fontScale, color, thickness, cv2.LINE_AA)

        if len(boxes) > 0:
            # Si hay varios boxes se selecciona el box más cercano al anterior
            dist_min = 9999999
            for box in boxes:
                # Recorte de imágenes según box
                x_ini = box[0, 1]  # y
                y_ini = box[0, 0]  # x
                x_fin = box[1, 1]  # y+h
                y_fin = box[2, 0]  # x+w

                # img_seg_recortada = img_seg[x_ini:x_fin, y_ini:y_fin]
                #
                # # Añade fondo si la anchura es demasiado grande (todo: y no es una zona de ruido)
                # res_dist_transform = cv2.distanceTransform(img_seg_recortada, cv2.DIST_L2, 3)
                #
                # # Actualiza anchura_max solo en el primer intento (sin erosionar grises)
                # anchura_max_act = max(res_dist_transform[np.where(res_dist_transform > 0)])
                # # anchura_max = ((1- beta) * anchura_max_act) + (beta * anchura_max_ant)
                # # anchura_max_ant = anchura_max
                # # anchura_max = anchura_max / (1-beta**(cont+1))
                # # cont = cont + 1

                cx_act = x_ini + int((x_fin - x_ini)/2)
                cy_act = y_ini + int((y_fin - y_ini) / 2)

                dx = cx_act - cx_ant
                dy = cy_act - cy_ant
                dist_recorrida = math.sqrt((dx*dx)+(dy*dy))

                if dist_recorrida < dist_min:
                    dist_min = dist_recorrida
                    cx = cx_act
                    cy = cy_act
                    #anchura_max_ant = anchura_max_act

        if out.isOpened():
            cx_ini = cx - int(shape[0]/2)
            cy_ini = cy - int(shape[1]/2)

            if cy_ini+shape[1]>4024:
                cy_ini=4023-shape[0]
            if cy_ini<0:
                cy_ini=0
            if cx_ini+shape[0]>3036:
                cx_ini=3035-shape[0]
            if cx_ini<0:
                cx_ini=0
            out.write(gray[cx_ini:cx_ini+shape[0], cy_ini:cy_ini+shape[1]])
        else:
            print('Error no se puede crear el vídeo 1...')
            break

        poses.append((cx, cy))

        #print(path, '--------------------------n_frame: ', n_frame, len(boxes), dist_min, anchura_max_ant)
        if len(boxes) != 1:
            print(path+name_video, '--------------------------n_frame: ', n_frame, len(boxes), dist_min)
        n_frame = n_frame + 1
        gray_ant = gray.copy()
        cx_ant = cx
        cy_ant = cy

    np.save(path_out_name_video + '_poses.npy', poses)
    return poses


def show_video(path, name_video, shape):

    path_name_video = os.path.join(path, name_video)
    cap = cv2.VideoCapture(path_name_video + '_1.mp4')

    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps:", fps)

    totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print("totalNoFrames:", totalNoFrames)

    durationInSeconds = totalNoFrames / fps
    print("durationInSeconds:", durationInSeconds, "s")

    ini_frame = 0
    end_frame = int(totalNoFrames) - 1

    n_frame = ini_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, n_frame)

    if os.path.exists(path_name_video + "_ini.bmp") and os.path.exists(path_name_video + "_end.bmp") and os.path.exists(path_name_video + "_poses.npy"):

        gray_ini = cv2.imread(path_name_video + "_ini.bmp", 0)
        #gray_end = cv2.imread(path_name_video + "_end.bmp", 0)
        poses = np.load(path_name_video + '_poses.npy')
        img_result = np.zeros((gray_ini.shape[0], gray_ini.shape[1], 3), np.uint8)

        while (n_frame <= end_frame) and (cap.isOpened()):

            img_result[:, :, 1] = 255 - gray_ini.copy()
            #img_result[:, :, 2] = 0

            (cx, cy) = poses[n_frame]

            ret, img = cap.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            if n_frame == ini_frame:
                gray_ant = gray.copy()
                cx_ant = cx
                cy_ant = cy

            cv2.line(img_result, (cy_ant, cx_ant), (cy, cx), (255, 0, 0), thickness=2)

            cx_ini = cx - int(shape[0] / 2)
            cy_ini = cy - int(shape[1] / 2)
            img_result[cx_ini:cx_ini + shape[0], cy_ini:cy_ini + shape[1], 1] = 255 - gray

            cx_ini = cx_ant - int(shape[0] / 2)
            cy_ini = cy_ant- int(shape[1] / 2)
            img_result[cx_ini:cx_ini + shape[0], cy_ini:cy_ini + shape[1], 2] = 255 - gray_ant

            #cv2.imwrite(path_name_video + "_img_result_"+str(n_frame)+".bmp", img_result)
            cv2.imwrite(path_name_video + "_img_result.bmp", img_result)

            n_frame = n_frame + 1
            gray_ant = gray.copy()
            cx_ant = cx
            cy_ant = cy


class VideoCapture:

    def __init__(self, path, name_video, ext):

        path_name_video = os.path.join(path, name_video)
        if os.path.exists(path_name_video + ext):
            self.cap = cv2.VideoCapture(path_name_video + ext)
            width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)  # float `width`
            height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`
            self.shape = (int(height), int(width))
            self.n_frame = 0
            if os.path.exists(path_name_video + "_ini.bmp"):
                self.gray_ini = cv2.imread(path_name_video + "_ini.bmp", 0)
                if os.path.exists(path_name_video + "_poses.npy"):
                    self.poses = np.load(path_name_video + '_poses.npy')
                else:
                    print("Error: el fichero", path_name_video + "_poses.npy no existe.")
            else:
                print("Error: el fichero", path_name_video + "_ini.bmp no existe.")
        else:
            print("Error: el fichero", path_name_video + ext, 'no existe.')

    def set(self, feature, n_frame):
        self.cap.set(feature, n_frame)
        self.n_frame = n_frame

    def get(self, feature):
        value = self.cap.get(feature)
        return value

    def isOpened(self):
        value = self.cap.isOpened()
        return value

    def read(self):
        gray_act = self.gray_ini.copy()
        ret, img = self.cap.read()
        (cx, cy) = self.poses[self.n_frame]  #pos act
        cx_ini = cx - int(self.shape[0] / 2)
        cy_ini = cy - int(self.shape[1] / 2)
        self.gray_act[cx_ini:cx_ini + self.shape[0], cy_ini:cy_ini + self.shape[1]] = img
        self.n_frame += 1
        return ret, gray_act

def video_process(path, name_video, simplify):

    path_name_video = os.path.join(path, name_video)
    print('--------------------------path:', path_name_video)

    # data = np.load(path_name_video + '.npz', allow_pickle=True)
    # lst = data.files
    # for item in lst:
    #     print(item)
    #     print(data[item])

    if simplify:
        path_out = path.replace('egg_laying', 'egg_laying_new')
        path_out_name_video = os.path.join(path_out, name_video)
    else:
        path_out = path
        path_out_name_video = path_name_video

    if not os.path.exists(path_out_name_video + "_imgs"):
        print(path_out_name_video + "_imgs")
        os.makedirs(path_out_name_video + "_imgs")

    if not os.path.exists(path_out_name_video + "_rare_poses"):
        os.makedirs(path_out_name_video + "_rare_poses")

    cap = cv2.VideoCapture(path_name_video + '.mp4')

    fps = cap.get(cv2.CAP_PROP_FPS)
    # print("fps:", fps)

    totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    # print("totalNoFrames:", totalNoFrames)

    if totalNoFrames == 0.0:
        print('Error:', path_name_video, 'está vacio!')
        return

    durationInSeconds = totalNoFrames / fps
    # print("durationInSeconds:", durationInSeconds, "s")

    # start_time = time.time()

    ini_frame = 0
    end_frame = int(totalNoFrames) - 1

    eggs_dist_transform, img_changes_0, noise, gray_end = get_changes_red(path, name_video, cap, ini_frame, end_frame)

    # La posidión inicial es el centro de imagen o la posición final del video anterior
    cx_ant = int(eggs_dist_transform.shape[0]/2)
    cy_ant = int(eggs_dist_transform.shape[1]/2)
    init_pose = [cx_ant, cy_ant]
    num_video_ant = int(name_video) - 1
    name_video_ant = str(num_video_ant).zfill(6)
    path_out_name_video_ant = os.path.join(path_out, name_video_ant)
    if os.path.isfile(path_out_name_video_ant + '_poses.npy'):
        tabla_poses = np.load(path_out_name_video_ant + '_poses.npy')
        init_pose = tabla_poses[17999]

    # ini_frame = 16874
    # end_frame = 17436
    # frame_items = lib.process(path, cap, ini_frame, end_frame, eggs_dist_transform)

    #ini_frame = 2900 #todo: comentar
    #end_frame = 2970 #todo: comentar
    frame_items = process_in_detail(path, name_video, cap, ini_frame, end_frame, eggs_dist_transform, img_changes_0,
                                        noise, gray_end, init_pose, simplify=simplify)
    print(path_name_video, 'frame_items:', frame_items)

    with open(path_out_name_video + '_metadata_eggs_times.csv', 'w', newline='') as csvfile:
        fieldnames = ['full_data', 'cy', 'cx', 'area', 'ratio', 'dist_skel_egg', 'skel_lenght',
                      'ratio_skel_lenght_dist_min', 'blue_dist', 'sum_diff']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for items in frame_items:
            for item in items:
                sec = int(item[0] / fps)
                writer.writerow(
                    {'full_data': str(datetime.timedelta(seconds=sec)), 'cy': str(item[1]), 'cx': str(item[2]),
                     'area': str(item[3]), 'ratio': str(item[4]), 'dist_skel_egg': str(item[5]),
                     'skel_lenght': str(item[6]), 'ratio_skel_lenght_dist_min': str(item[7]), 'blue_dist': str(item[8]),
                     'sum_diff': str(item[9])})

    with open(path_out_name_video + '_metadata_eggs_frames.csv', 'w', newline='') as csvfile:
        fieldnames = ['frame_num', 'cy', 'cx', 'area', 'ratio', 'dist_skel_egg', 'skel_lenght',
                      'ratio_skel_lenght_dist_min', 'blue_dist', 'sum_diff']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for items in frame_items:
            for item in items:
                writer.writerow(
                    {'frame_num': str(item[0]), 'cy': str(item[1]), 'cx': str(item[2]), 'area': str(item[3]),
                     'ratio': str(item[4]), 'dist_skel_egg': str(item[5]), 'skel_lenght': str(item[6]),
                     'ratio_skel_lenght_dist_min': str(item[7]), 'blue_dist': str(item[8]), 'sum_diff': str(item[9])})

    return frame_items

## Para lanzar todos los vídeos de un ensayo en paralelo
def thread_process_video(path, name_video, simplify):
    frame_items =  video_process(path, name_video, simplify)

def is_assay_finish(assay_path):
    finished = False
    filename = os.path.join(assay_path, 'metadata_eggs_final.csv')
    if os.path.isfile(filename):
        finished = True
    return finished

def is_video_saved(videos_path, name_video):
    saved = False
    path_out_name_video = os.path.join(videos_path, name_video)
    if os.path.isfile(path_out_name_video + "_metadata_eggs_frames_final.csv"):
        saved = True
    return saved

def is_process_finish(originals_path, name_video):
    processed = False
    path_out = originals_path.replace('egg_laying', 'egg_laying_new')
    path_out_name_video = os.path.join(path_out, name_video)
    if os.path.isfile(path_out_name_video + "_img_result_tracking.bmp"):
        processed = True
    return processed

def is_process_init(originals_path, name_video):
    processed = False
    path_out = originals_path.replace('egg_laying', 'egg_laying_new')
    path_out_name_video = os.path.join(path_out, name_video)
    if os.path.isfile(path_out_name_video + "_imgs/gray_ini_sin_gusanos.bmp"):
    #if os.path.isfile(path_out_name_video + "_img_result_tracking.bmp"):
        processed = True
    return processed

def thread_process_assay(working_path, working_assay, originals_videos):
    originals_path = os.path.join(working_path, working_assay)
    for originals_video in originals_videos:
        name_video = originals_video.split('.')[0]
        if not is_process_init(originals_path, name_video):
            # x = threading.Thread(target=lib.thread_process_video,
            #                      args=(originals_path + '/', name_video, True,),
            #                      daemon=True)
            # x.start()
            thread_process_video(originals_path + '/', name_video, True)
        else:
            path_name_video = os.path.join(originals_path, name_video)
            print('--------------------------path:', path_name_video)
            print('This video has been processed. Delete the processed folder if you want to process it again...')

class Evaluator:

    def __init__(self, path, names_videos):

        self.path = path
        self.evaluated_videos = []

        self.tp = []
        self.fp = []
        self.fn = []
        self.fn_criticos = []

        self.seconds_per_video = 12*60 # todo: ajustar un video de 1 hora son 12 minutos

        # Leer ground true
        names_videos.sort()
        self.read_gt()

        for name_video in names_videos:
            self.evaluate_video(name_video)

    def read_gt(self):
        if 'completos' in self.path:
            file_name_gt = os.path.join(self.path, 'metadata_eggs.csv')
            self.df_gt = pd.read_csv(file_name_gt)
            self.df_gt['new_full_data'] = pd.to_timedelta(self.df_gt['full_data']).dt.total_seconds().map('{:,.2f}'.format) # Pasar a segundos
        elif 'borde' in self.path:
            file_name_gt = os.path.join(self.path, 'metadata_eggs_gt.xlsx')
            self.df_gt = pd.read_excel(file_name_gt, engine='openpyxl', header=None)
            self.df_gt['new_full_data'] = pd.TimedeltaIndex(self.df_gt[0].astype("str")).total_seconds().map('{:,.2f}'.format)
        else:
            file_name_gt = os.path.join(self.path, 'metadata_eggs_gt.csv')
            self.df_gt = pd.read_csv(file_name_gt)
            self.df_gt['new_full_data'] = pd.to_timedelta(self.df_gt['full_data']).dt.total_seconds().map('{:,.2f}'.format) # Pasar a segundos

        self.df_gt['new_full_data'] = self.df_gt['new_full_data'].str.replace(',', '').astype(float)

        #print('Ground True:', self.df_gt)

    def evaluate_video(self, name_video):
        video_number = int(name_video)
        if 'borde' in self.path:
            video_number = 0

        rango = (video_number * self.seconds_per_video, ((video_number + 1) * self.seconds_per_video) - 1)
        # print('Rango:', rango)
        res_gt = self.df_gt.loc[(self.df_gt['new_full_data'] >= rango[0]) & (self.df_gt['new_full_data'] <= rango[1])]
        # print(res_gt)

        self.evaluated_videos.append(name_video)
        path_out = self.path.replace('egg_laying', 'egg_laying_new')

        file_name_frames = os.path.join(path_out, name_video + '_metadata_eggs_frames_final.csv')
        if not os.path.isfile(file_name_frames):
            file_name_frames = os.path.join(path_out, name_video + '_metadata_eggs_frames.csv')
        df_frames = pd.read_csv(file_name_frames)
        #print(df_frames)
        df_frames['new_full_data'] = df_frames['frame_num'].astype(float)
        df_frames['new_full_data'] = df_frames['new_full_data']/25 + (video_number * self.seconds_per_video)
        res_est = df_frames['new_full_data'].tolist()

        # file_name = os.path.join(path_out, name_video + '_metadata_eggs_times.csv')
        # df = pd.read_csv(file_name)
        # # Pasar a segundos
        # df['new_full_data'] = pd.to_timedelta(df['full_data']).dt.total_seconds().map('{:,.2f}'.format)
        # df['new_full_data'] = df['new_full_data'].str.replace(',', '').astype(float)
        # df['new_full_data'] = df['new_full_data'] + (video_number * self.seconds_per_video)
        # res_est = df['new_full_data'].tolist()

        for data_gt in res_gt['new_full_data']:
            match = False
            for data_est in res_est:
                if abs(data_gt-data_est) <= 1:
                    self.tp.append((data_est, data_gt))
                    res_est.remove(data_est)
                    match = True
                    break

            if not match:
                self.fn.append(data_gt)
                match_previous = False
                for _, d_gt in self.tp:
                    if abs(data_gt - d_gt) <= 1:
                        match_previous = True
                        break
                if not match_previous:
                    n_frame = (data_gt - (video_number * self.seconds_per_video))*25
                    self.fn_criticos.append((data_gt, video_number, int(n_frame)))

        for data_est in res_est:
            self.fp.append(data_est)

    def show_results(self):

        print('Evaluator path', self.path)
        print(self.evaluated_videos)
        print('-------------')

        num_tp = len(self.tp)
        num_fn = len(self.fn)
        num_fp = len(self.fp)
        num_tn = 18000 - num_tp - num_fn - num_fp

        print('Cofusion matrix:')
        print(num_tp, num_fp)
        print(num_fn, num_tn)

        print('tp', self.tp)
        #n_frame = (data_gt - (video_number * self.seconds_per_video)) * 25
        print('fn', self.fn, '->', [(int(seconds / self.seconds_per_video), int((seconds % self.seconds_per_video)*25)) for seconds in self.fn])
        print('fp', self.fp, '->', [(int(seconds / self.seconds_per_video), int((seconds % self.seconds_per_video)*25)) for seconds in self.fp])

        print('fn_criticos', self.fn_criticos)

        print('-------------')








