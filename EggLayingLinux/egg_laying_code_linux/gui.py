import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog
from tkinter import ttk, messagebox
import os
import time
import datetime
import math
import lib
import threading
import pandas as pd
import csv

def strfdelta(tdelta):
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    fmt = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
    return fmt

class VideoPlayer:
    def __init__(self, working_path, checked_path, working_assay):

        self.track_eggs_frames = []
        self.ok_eggs_frames = []
        self.nok_eggs_frames = []

        # Undo
        self.eggs_ok_listbox_previous = []
        self.eggs_nok_listbox_previous = []

        self.speed_factor = 1 # de momento no se utiliza
        self.exist_ventana_flotante = False
        self.playing_video = False
        self.inc = 1

        # Activar la carpeta de videos originales (la carpeta donde se almacenan los resultados se define de manera automática en lib.process_in_detail)
        self.set_originals_path(working_path, working_assay, True)

        # Activar la carpeta de los resultados procesados a chequear -> folder_path
        folder_path = os.path.join(checked_path, working_assay)
        self.set_folder_path(folder_path, True)

        # Tamaño del canvas donde se muestra el vídeo
        self.scale = 4.0
        img_width = 128
        img_height = 128
        max_size_window = img_width*self.scale

        self.seconds_per_video = 12 * 60  # todo: ajustar un video de 1 hora son 12 minutos

        if self.cap.isOpened():
            img_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            img_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.scale = max_size_window / max(img_width, img_height)

        self.size_window = (int(img_width*self.scale), int(img_height*self.scale))

        self.egg_pose = (0, 0)

        # Interfaz gráfica
        self.root = tk.Tk()
        self.root.title("Egg-laying Videos Player")
        #self.root.wm_attributes('-zoomed', 1)

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill='both', expand='yes')

        self.p1 = ttk.Frame(self.nb)
        self.p2 = ttk.Frame(self.nb)
        self.nb.add(self.p1, text='Processing')
        self.nb.add(self.p2, text='Checking')

        # *******************************************
        # ************* P1 (Processing) *************
        # *******************************************
        self.fm01 = tk.Frame(self.p1)
        self.fm01.pack(expand=True, side=tk.LEFT)

        self.fm02 = tk.Frame(self.p1)
        self.fm02.pack(expand=True, side=tk.RIGHT)

        self.working_folder_label = tk.Label(self.fm01, text="Working folder: " + self.working_path,
                                     anchor="center", bg="gray")
        self.working_folder_label.pack(pady=1)

        self.select_working_folder_button = tk.Button(self.fm01, text="Change working folder", command=self.select_working_path)
        self.select_working_folder_button.pack(pady=5)

        self.working_assays_label = tk.Label(self.fm01, text="Select assay from next list:", anchor="center", bg="gray")
        self.working_assays_label.pack(pady=1)

        # Seleccionar la lista de ensayos dentro de una carpeta
        self.working_assays_listbox = tk.Listbox(self.fm01, exportselection=False)
        self.working_assays_listbox.pack()

        # Mostrar ensayos en la lista
        path_out = self.working_path.replace('egg_laying', 'egg_laying_new')
        for idx, item in enumerate(self.working_assays):
            self.working_assays_listbox.insert(tk.END, item)
            assay_path = os.path.join(path_out, item)
            if lib.is_assay_finish(assay_path):
                self.working_assays_listbox.itemconfig(idx, {'bg': 'LightCyan2'})

        # Vincular evento de clic de ratón a la función
        self.working_assays_listbox.bind('<Button-1>', self.set_assay_path)

        self.process_all_assays_button = tk.Button(self.fm01, text="Process all assays", command=self.process_assays)
        self.process_all_assays_button.pack(pady=5)

        self.save_all_assays_button = tk.Button(self.fm01, text="Save results of all assays", command=self.save_all_assays_result)
        self.save_all_assays_button.pack(pady=5)
        #---------------

        self.originals_folder_label = tk.Label(self.fm02, text="Selected Assay folder: " + self.working_assay,
                                     anchor="center", bg="gray")
        self.originals_folder_label.pack(pady=1)

        self.select_assay_button = tk.Button(self.fm02, text="Change assay folder", command=self.select_assay_path)
        self.select_assay_button.pack(pady=5)

        self.originals_videos_label = tk.Label(self.fm02, text="Select video from next list:", anchor="center", bg="gray")
        self.originals_videos_label.pack(pady=1)

        # Seleccionar la lista de videos dentro de una carpeta
        self.originals_videos_listbox = tk.Listbox(self.fm02, exportselection=False)
        self.originals_videos_listbox.pack()

        # Mostrar videos en la lista
        originals_path = os.path.join(self.working_path, self.working_assay)
        for idx, item in enumerate(self.originals_videos):
            self.originals_videos_listbox.insert(tk.END, item)
            name_video = item.split('.')[0]
            if lib.is_process_finish(originals_path, name_video):
                self.originals_videos_listbox.itemconfig(idx, {'bg': 'LightCyan2'})

        # Vincular evento de clic de ratón a la función
        self.originals_videos_listbox.bind('<Button-1>', self.process_video)

        self.process_all_videos_button = tk.Button(self.fm02, text="Process all videos", command=self.process_videos)
        self.process_all_videos_button.pack(pady=5)

        self.save_all_videos_button = tk.Button(self.fm02, text="Save results of this assay", command=self.save_assay_result)
        self.save_all_videos_button.pack(pady=5)

        # *******************************************
        # ************* P2 (Checking) *************
        # *******************************************
        # self.root.grid_rowconfigure(0, weight=5, uniform="rows_g1")
        # self.root.grid_rowconfigure(1, weight=1, uniform="rows_g1")
        # self.root.grid_columnconfigure(0, weight=1,  uniform="cols_g1")
        # self.root.grid_columnconfigure(1, weight=2,  uniform="cols_g1")
        # self.root.grid_columnconfigure(2, weight=1, uniform="cols_g1")
        self.p2.grid_rowconfigure(0, weight=5, uniform="rows_g1")
        self.p2.grid_rowconfigure(1, weight=1, uniform="rows_g1")
        self.p2.grid_columnconfigure(0, weight=1,  uniform="cols_g1")
        self.p2.grid_columnconfigure(1, weight=2,  uniform="cols_g1")
        self.p2.grid_columnconfigure(2, weight=1, uniform="cols_g1")

        # ************* Frame1 (0,0) *************
        #self.fm1 = tk.Frame(self.root, bg="gray")
        self.fm1 = tk.Frame(self.p2, bg="gray")
        self.fm1.grid(row=0, column=0, sticky='nsew')

        self.fm11 = tk.Frame(self.fm1, bg="gray")
        self.fm11.pack(expand=True, side=tk.LEFT)

        self.fm12 = tk.Frame(self.fm1, bg="gray")
        self.fm12.pack(expand=True, side=tk.RIGHT)

        self.eggs_nok_label = tk.Label(self.fm11, text="egg-layed frames (NOK)", anchor="center", bg="gray", fg='coral2')
        self.eggs_nok_label.pack()

        self.eggs_nok_listbox = tk.Listbox(self.fm11, exportselection=False)
        self.eggs_nok_listbox.pack()
        # for item in self.nok_eggs_frames:
        #     self.eggs_nok_listbox.insert(tk.END, item)

        # Vincular evento de clic de ratón a la función
        self.eggs_nok_listbox.bind('<Button-1>', self.select_nok_0)
        self.eggs_nok_listbox.bind('<Up>', self.select_nok_Up)
        self.eggs_nok_listbox.bind('<Down>', self.select_nok_Down)
        self.eggs_nok_listbox.bind('<Left>', self.prev_frame_Left)
        self.eggs_nok_listbox.bind('<Right>', self.next_frame_Right)

        self.button_move_OK = tk.Button(self.fm11, text="Move to OK >>", command=self.move_selected_item_OK)
        self.button_move_OK.pack(pady=5)

        self.button_delete_NOK = tk.Button(self.fm11, text="Delete", command=self.delete_item_NOK)
        self.button_delete_NOK.pack(pady=5)

        self.button_undo_NOK = tk.Button(self.fm11, text="Undo", command=self.undo_item_NOK)
        self.button_undo_NOK.pack(pady=5)

        self.layedEgg_label = tk.Label(self.fm11, text="egg-layed frame", anchor="center", bg="gray")
        self.layedEgg_label.pack()

        self.canvas_egg = tk.Canvas(self.fm11, width=128, height=128)
        self.canvas_egg.pack()

        self.edit_layedEgg_entry = tk.Entry(self.fm11, width=10, justify='center')
        self.edit_layedEgg_entry.pack(pady=5)
        self.edit_layedEgg_entry.bind('<Return>', self.edit_item_layedEgg_Return)

        self.button_edit_layedEgg = tk.Button(self.fm11, text="Edit & Order", command=self.edit_item_layedEgg)
        self.button_edit_layedEgg.pack(pady=5)

        self.eggs_ok_label = tk.Label(self.fm12, text="egg-layed frames (OK)", anchor="center", bg="gray", fg='aquamarine1')
        self.eggs_ok_label.pack()

        self.eggs_ok_listbox = tk.Listbox(self.fm12, exportselection=False)
        self.eggs_ok_listbox.pack()

        # Vincular evento de clic de ratón a la función
        self.eggs_ok_listbox.bind('<Button-1>', self.select_ok_0)
        self.eggs_ok_listbox.bind('<Button-3>', self.select_ok_1)
        self.eggs_ok_listbox.bind('<Up>', self.select_ok_Up)
        self.eggs_ok_listbox.bind('<Down>', self.select_ok_Down)
        self.eggs_ok_listbox.bind('<Left>', self.prev_frame_Left)
        self.eggs_ok_listbox.bind('<Right>', self.next_frame_Right)

        self.button_duplicate_OK = tk.Button(self.fm12, text="x2", command=self.duplicate_item_OK)
        self.button_duplicate_OK.pack(pady=5)

        self.button_delete_OK = tk.Button(self.fm12, text="Delete", command=self.delete_item_OK)
        self.button_delete_OK.pack(pady=5)

        self.button_undo_OK = tk.Button(self.fm12, text="Undo", command=self.undo_item_OK)
        self.button_undo_OK.pack(pady=5)

        self.trackedEgg_label = tk.Label(self.fm12, text="tracked-layed frame", anchor="center", bg="gray")
        self.trackedEgg_label.pack()

        self.canvas_track = tk.Canvas(self.fm12, width=128, height=128)
        self.canvas_track.pack()

        self.edit_trackedEgg_entry = tk.Entry(self.fm12, width=10, justify='center')
        self.edit_trackedEgg_entry.pack(pady=5)
        self.edit_trackedEgg_entry.bind('<Return>', self.edit_item_trackedEgg_Return)

        self.button_edit_trackedEgg = tk.Button(self.fm12, text="Edit", command=self.edit_item_trackedEgg)
        self.button_edit_trackedEgg.pack(pady=5)

        self.imgs_pair = []
        self.imgs_pair.append(np.ones((128, 128, 3), np.uint8)*255)
        self.imgs_pair.append(np.ones((128, 128, 3), np.uint8)*255)

        # ************* Frame2 (0,1) *************
        #self.fm2 = tk.Frame(self.root, bg="gray")
        self.fm2 = tk.Frame(self.p2, bg="gray")
        self.fm2.grid(row=0, column=1, sticky='nsew')

        self.fm21 = tk.Frame(self.fm2, bg="gray")
        self.fm21.pack()

        self.video_label = tk.Label(self.fm21, text="Video: "+self.video, anchor="center", bg="gray")
        self.video_label.pack(side=tk.LEFT, padx=1, pady=1)

        self.frame_label = tk.Label(self.fm21, text="Frame: {}".format(self.frame_number), anchor="center", bg="gray")
        self.frame_label.pack(side=tk.LEFT, padx=1, pady=1)

        sec = (self.video_number * 12 * 60) + (int(self.frame_number) / 25)
        self.time_label = tk.Label(self.fm21, text="Time: " + strfdelta(datetime.timedelta(seconds=sec)), anchor="center", bg="gray")
        self.time_label.pack(side=tk.LEFT, padx=1, pady=1)

        self.canvas = tk.Canvas(self.fm2, width=self.size_window[0], height=self.size_window[1])
        self.canvas.pack()

        # ************* Frame3 (0,2) *************
        #self.fm3 = tk.Frame(self.root, bg="gray")
        self.fm3 = tk.Frame(self.p2, bg="gray")
        self.fm3.grid(row=0, column=2, sticky='nsew')

        self.folder_label = tk.Label(self.fm3, text="Selected Assay folder: "+self.videos_path.split('/')[-1], anchor="center", bg="gray")
        self.folder_label.pack(pady=1)

        self.select_button = tk.Button(self.fm3, text="Change assay folder", command=self.select_folder_path)
        self.select_button.pack(pady=5)

        self.videos_label = tk.Label(self.fm3, text="Select video from next list:", anchor="center", bg="gray")
        self.videos_label.pack(pady=1)

        # Seleccionar la lista de videos dentro de una carpeta
        self.videos_listbox = tk.Listbox(self.fm3, exportselection=False)
        self.videos_listbox.pack(pady=5)

        self.save_button = tk.Button(self.fm3, text="Save results of this video", command=self.save_final_results)
        self.save_button.pack()

        # Mostrar videos en la lista
        for idx, item in enumerate(self.videos):
            self.videos_listbox.insert(tk.END, item)
            name_video = item.split('.')[0]
            if lib.is_video_saved(self.videos_path, name_video):
                self.videos_listbox.itemconfig(idx, {'bg': 'LightCyan2'})

        # Vincular evento de clic de ratón a la función
        self.videos_listbox.bind('<Button-1>', self.select_video)

        # ************* Frame4 (1,0) *************
        #self.fm4 = tk.Frame(self.root, bg="gray")
        self.fm4 = tk.Frame(self.p2, bg="gray")
        self.fm4.grid(row=1, column=0, sticky='nsew')

        self.frame_label_entry = tk.Label(self.fm4, text="Enter frame number:", bg="gray")
        self.frame_label_entry.pack(side=tk.LEFT, padx=1, pady=1)

        self.frame_entry = tk.Entry(self.fm4, width=5, justify='center')
        self.frame_entry.pack(side=tk.LEFT, padx=1, pady=1)
        self.frame_entry.bind('<Return>', self.go_to_frame_Return)

        self.go_to_frame_button = tk.Button(self.fm4, text="Go to", anchor="center", command=self.go_to_frame)
        self.go_to_frame_button.pack(side=tk.LEFT, padx=1, pady=1)

        # ************* Frame5 (1,1) *************
        #self.fm5 = tk.Frame(self.root, bg="gray")
        self.fm5 = tk.Frame(self.p2, bg="gray")
        self.fm5.grid(row=1, column=1, sticky='nsew')

        self.fm51 = tk.Frame(self.fm5, bg="gray")
        self.fm51.pack()

        self.prev_icon = ImageTk.PhotoImage(Image.open("prev_icon.png"))
        self.prev_button = tk.Button(self.fm51, image=self.prev_icon, anchor="center", command=self.pause_video, bd=0)
        self.prev_button.pack(side=tk.LEFT, padx=1, pady=1)

        self.prev_button.bind('<ButtonPress-1>', self.backward_video_lento)
        self.prev_button.bind('<Button-3>', self.backward_video_lento)

        self.pause_icon = ImageTk.PhotoImage(Image.open("pause_icon.png"))
        self.pause_button = tk.Button(self.fm51, image=self.pause_icon, anchor="center", command=self.pause_video, bd=0)
        self.pause_button.pack(side=tk.LEFT, padx=1, pady=1)

        self.next_icon = ImageTk.PhotoImage(Image.open("next_icon.png"))
        self.next_button = tk.Button(self.fm51, image=self.next_icon, anchor="center", command=self.pause_video, bd=0)
        self.next_button.pack(side=tk.LEFT, padx=1, pady=1)

        self.next_button.bind('<ButtonPress-1>', self.forward_video_lento)
        self.next_button.bind('<Button-3>', self.forward_video_lento)

        self.fm52 = tk.Frame(self.fm5, bg="gray")
        self.fm52.pack()

        self.backward_icon = ImageTk.PhotoImage(Image.open("backward_icon.png"))
        self.backward_button = tk.Button(self.fm52, image=self.backward_icon, anchor="center", command=self.pause_video)
        self.backward_button.pack(side=tk.LEFT, padx=1, pady=1)

        self.backward_button.bind('<ButtonPress-1>', self.backward_video)
        self.backward_button.bind('<Button-3>', self.backward_video)

        self.inc_entry = tk.Entry(self.fm52, width=10, justify='center')
        self.inc_entry.pack(side=tk.LEFT, padx=1, pady=1)
        self.inc_entry.insert(0, '5')

        self.forward_icon = ImageTk.PhotoImage(Image.open("forward_icon.png"))
        self.forward_button = tk.Button(self.fm52, image=self.forward_icon, anchor="center", command=self.pause_video)
        self.forward_button.pack(side=tk.LEFT, padx=1, pady=1)

        self.forward_button.bind('<ButtonPress-1>', self.forward_video)
        self.forward_button.bind('<Button-3>', self.forward_video)

        # ************* Frame6 (1,2) *************
        #self.fm6 = tk.Frame(self.root, bg="gray")
        self.fm6 = tk.Frame(self.p2, bg="gray")
        self.fm6.grid(row=1, column=2, sticky='nsew')

        self.mark_egg = tk.IntVar(value = 1)
        self.mark_egg_checkbutton = tk.Checkbutton(self.fm6, text='Mark nearest egg', variable=self.mark_egg, onvalue=1, offvalue=0, command=self.show_mark_egg)
        self.mark_egg_checkbutton.pack()

        self.show_track = tk.IntVar()
        self.show_track_checkbutton = tk.Checkbutton(self.fm6, text='Show track', variable=self.show_track, onvalue=1, offvalue=0, command=self.show_trajectory)
        self.show_track_checkbutton.pack()

        self.show_worm_details = tk.IntVar()
        self.show_details_checkbutton = tk.Checkbutton(self.fm6, text='Show worm details', variable=self.show_worm_details, onvalue=1, offvalue=0, command=self.show_details)
        self.show_details_checkbutton.pack()

        self.root.bind("<KeyRelease>", self.fun)

    def fun(self, event):

        if event.keysym == 'p':
            self.nb.select(self.p1)
            self.working_assays_listbox.focus()
            #self.set_assay_path()

        elif event.keysym == 'c':
            self.nb.select(self.p2)
            self.videos_listbox.focus()
            #self.select_video()

        elif event.keysym == 'o':
            self.nb.select(self.p2)
            self.eggs_ok_listbox.focus()
            self.eggs_ok_listbox.selection_clear(0, 'end')
            frame_items = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
            if len(frame_items):
                self.eggs_ok_listbox.selection_set(0)
                self.eggs_ok_listbox.activate(0)
                #self.eggs_ok_listbox.select_set(0)  # This only sets focus on the first item.
                #self.eggs_ok_listbox.event_generate("<<ListboxSelect>>")
                #self.eggs_ok_listbox.
                self.select_ok((0,), 0)

        elif event.keysym == 'n':
            self.nb.select(self.p2)
            self.eggs_nok_listbox.focus()
            self.eggs_nok_listbox.selection_clear(0, 'end')
            frame_items = list(self.eggs_nok_listbox.get(0, self.eggs_nok_listbox.size() - 1))
            if len(frame_items):
                self.eggs_nok_listbox.selection_set(0)
                self.eggs_nok_listbox.activate(0)
                #self.eggs_nok_listbox.select_set(0)  # This only sets focus on the first item.
                #self.eggs_nok_listbox.event_generate("<<ListboxSelect>>")
                self.select_nok((0,))

        elif event.keysym == 'plus':
            self.nb.select(self.p2)
            self.inc = int(self.inc_entry.get()) + 1
            self.inc_entry.delete(0, "end")
            self.inc_entry.insert(0, str(self.inc))

        elif event.keysym == 'minus':
            self.nb.select(self.p2)
            self.inc = int(self.inc_entry.get()) - 1
            self.inc_entry.delete(0, "end")
            self.inc_entry.insert(0, str(self.inc))

        #print(event.keysym, event.keysym == 'a')
        #print(event)

    def read_processed_videos_from_folder(self, originals_path):
        videos = []
        if os.path.exists(originals_path):
            for filename in os.listdir(originals_path):
                filepath = os.path.join(originals_path, filename)
                if os.path.isfile(filepath) and filename.endswith(('.mp4', '.avi', '.mov')):
                    #print('file size:', os.path.getsize(filepath))
                    if os.path.getsize(filepath) > 5000:
                        name_video = filename.split('.')[0]
                        if lib.is_process_finish(originals_path.replace('_new', ''), name_video):
                            videos.append(filename)
            videos.sort()

        return videos

    def read_videos_from_folder(self, originals_path):
        videos = []
        if os.path.exists(originals_path):
            for filename in os.listdir(originals_path):
                filepath = os.path.join(originals_path, filename)
                if os.path.isfile(filepath) and filename.endswith(('.mp4', '.avi', '.mov')):
                    #print('file size:', os.path.getsize(filepath))
                    if os.path.getsize(filepath) > 960000:
                        videos.append(filename)
            videos.sort()

        return videos

    def set_originals_path(self, working_path, working_assay, init):

        if os.path.exists(working_path):
            self.working_path = working_path
            with open("rutas.txt", "w") as f:
                f.write(working_path)
        else:
            self.working_path = '/'

        folders = os.listdir(self.working_path)
        self.working_assays = []
        for folder in folders:
            if os.path.isdir(os.path.join(self.working_path,folder)):
                self.working_assays.append(folder)
        self.working_assays.sort()

        if not init:
            self.working_assays_listbox.delete(0, tk.END)

            # Mostrar ensayos en la lista
            path_out = self.working_path.replace('egg_laying', 'egg_laying_new')
            for idx, item in enumerate(self.working_assays):
                self.working_assays_listbox.insert(tk.END, item)
                assay_path = os.path.join(path_out, item)
                if lib.is_assay_finish(assay_path):
                    self.working_assays_listbox.itemconfig(idx, {'bg': 'LightCyan2'})

        originals_path = os.path.join(working_path, working_assay)
        if (working_assay != '') and os.path.exists(originals_path):
            self.working_assay = working_assay
        else:
            if len(self.working_assays) > 0:
                self.working_assay = self.working_assays[0] # Seleccionar el primer ensayo
            else:
                self.working_assay = ''

        if not init:
            self.originals_folder_label.config(text="Selected Assay: " + self.working_assay)

        print("Selected working folder:", self.working_path)

        originals_path = os.path.join(self.working_path, self.working_assay)
        self.originals_videos = self.read_videos_from_folder(originals_path)

        print("Selected assay folder:", originals_path)

        if not init:
            # Mostrar videos en la lista
            self.originals_videos_listbox.delete(0, tk.END)
            for idx, item in enumerate(self.originals_videos):
                self.originals_videos_listbox.insert(tk.END, item)
                name_video = item.split('.')[0]
                if lib.is_process_finish(originals_path, name_video):
                    self.originals_videos_listbox.itemconfig(idx, {'bg': 'LightCyan2'})

    def set_folder_path(self, folder_path, init):
        if os.path.exists(folder_path):
            self.videos_path = folder_path
        else:
            self.videos_path = '/'

        print("Selected checked folder:", self.videos_path)

        self.videos = self.read_processed_videos_from_folder(self.videos_path)
        self.video = ""

        if not init:
            self.videos_listbox.delete(0, tk.END)

            # Mostrar videos en la lista
            for idx, item in enumerate(self.videos):
                self.videos_listbox.insert(tk.END, item)
                name_video = item.split('.')[0]
                if lib.is_video_saved(self.videos_path, name_video):
                    self.videos_listbox.itemconfig(idx, {'bg': 'LightCyan2'})

            # Seleccionar el primer video
            self.index_video = 0
            if len(self.videos) > 0:
                self.video = self.videos[self.index_video]

        self.open_video(init, 0)

    def select_working_path(self):
        working_path = filedialog.askdirectory(initialdir=self.working_path)
        if working_path:
            self.working_path = working_path
            self.working_folder_label.config(text = "Working folder: " + working_path)
            self.set_originals_path(working_path, '', False)

    def select_assay_path(self):
        assay_path = filedialog.askdirectory(initialdir=self.working_path)
        if assay_path:
            self.working_assay = assay_path.split('/')[-1]
            print("Selected Working Assay:", self.working_assay)

            originals_path = os.path.join(self.working_path, self.working_assay)
            self.set_originals_path(self.working_path, self.working_assay, False)
            self.originals_folder_label.config(text = "Selected Assay: " + self.working_assay)

    def set_assay_path(self, event):
        # Obtener el índice del elemento seleccionado
        self.working_assays_listbox.selection_clear(0, tk.END)
        self.working_assays_listbox.selection_set(self.working_assays_listbox.nearest(event.y))
        self.working_assays_listbox.activate(self.working_assays_listbox.nearest(event.y))
        index_assay = self.working_assays_listbox.curselection()

        if index_assay:
            # Obtener el valor del elemento seleccionado
            self.working_assay = self.working_assays_listbox.get(index_assay)
            self.working_index_assay = index_assay[0]
            #print("Indice seleccionado:", self.working_index_assay)
            print("Selected Working Assay:", self.working_assay)

            originals_path = os.path.join(self.working_path, self.working_assay)
            self.set_originals_path(self.working_path, self.working_assay, False)
            self.originals_folder_label.config(text = "Selected Assay: " + self.working_assay)

    def select_folder_path(self):
        folder_path = filedialog.askdirectory(initialdir=self.videos_path)
        if folder_path:
            self.set_folder_path(folder_path, False)

    def save_all_assays_result(self):
        for working_assay in self.working_assays:
            self.set_originals_path(self.working_path, working_assay, False)
            # Comprobación si esta carpeta es un ensayo
            videos = self.read_videos_from_folder(os.path.join(self.working_path, working_assay))
            if len(videos) > 0:
                self.save_assay_result()
            else:
                print('En', os.path.join(self.working_path, working_assay), 'no hay videos!')

    def save_assay_result(self):

        originals_path = os.path.join(self.working_path, self.working_assay)
        path_out = originals_path.replace('egg_laying', 'egg_laying_new')
        output_filename = os.path.join(path_out, 'metadata_eggs_final.csv')

        with open(output_filename, 'w', newline='') as csvfile:
            fieldnames = ['full_data', 'video', 'frame_num']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for idx, item in enumerate(self.originals_videos):
                name_video = item.split('.')[0]
                video_number = int(name_video)
                if lib.is_video_saved(path_out, name_video):
                    file_name_frames = os.path.join(path_out, name_video + '_metadata_eggs_frames_final.csv')
                    df_frames = pd.read_csv(file_name_frames)
                    #print(df_frames)
                    df_frames['new_full_data'] = df_frames['frame_num'].astype(float)
                    df_frames['new_full_data'] = df_frames['new_full_data']/25 + (video_number * self.seconds_per_video)
                    res_est = df_frames['new_full_data'].tolist()

                    for idx, sec in enumerate(res_est):
                        writer.writerow({'full_data': strfdelta(datetime.timedelta(seconds=sec)),
                                         'video': str(video_number),
                                         'frame_num': str(df_frames['frame_num'].values[idx])
                                         })

    def save_final_results_video(self, path_out_name_video, fps):
        with open(path_out_name_video + '_metadata_eggs_times_final.csv', 'w', newline='') as csvfile:
            fieldnames = ['full_data']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            frame_items = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
            for items in frame_items:
                item = items.split('.')
                sec = int(int(item[0]) / fps)
                writer.writerow({'full_data': str(datetime.timedelta(seconds=sec))})

        with open(path_out_name_video + '_metadata_eggs_frames_final.csv', 'w', newline='') as csvfile:
            fieldnames = ['frame_num']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for items in frame_items:
                item = items.split('.')
                writer.writerow({'frame_num': str(item[0])})

    def save_final_results(self):
        trozos = self.video.split('.')
        path_out_name_video = self.videos_path + '/' + trozos[0]
        self.save_final_results_video(path_out_name_video, 25)

        # Mostrar videos en la lista
        self.videos_listbox.delete(0, tk.END)
        for idx, item in enumerate(self.videos):
            self.videos_listbox.insert(tk.END, item)
            name_video = item.split('.')[0]
            if lib.is_video_saved(self.videos_path, name_video):
                self.videos_listbox.itemconfig(idx, {'bg': 'LightCyan2'})

    def save_results_ok(self):
        trozos = self.video.split('.')

        actual_ok_list = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
        ok_eggs_frames = []
        for pair in actual_ok_list:
            frames_str = pair.split('.')
            ok_eggs_frames.append(np.array([int(frames_str[0]),  int(frames_str[1])]))
        np.save(self.videos_path + '/' + trozos[0] + '_ok_eggs_frames.npy', ok_eggs_frames)

    def save_results_nok(self):
        trozos = self.video.split('.')

        actual_nok_list = list(self.eggs_nok_listbox.get(0, self.eggs_nok_listbox.size() - 1))
        nok_eggs_frames = []
        for frame_str in actual_nok_list:
            nok_eggs_frames.append(int(frame_str))
        np.save(self.videos_path + '/' + trozos[0] + '_nok_eggs_frames.npy', nok_eggs_frames)

    def save_results(self):
        trozos = self.video.split('.')

        actual_ok_list = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
        ok_eggs_frames = []
        for pair in actual_ok_list:
            frames_str = pair.split('.')
            ok_eggs_frames.append(np.array([int(frames_str[0]),  int(frames_str[1])]))
        np.save(self.videos_path + '/' + trozos[0] + '_ok_eggs_frames.npy', ok_eggs_frames)

        actual_nok_list = list(self.eggs_nok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
        nok_eggs_frames = []
        for frame_str in actual_nok_list:
            nok_eggs_frames.append(int(frame_str))
        np.save(self.videos_path + '/' + trozos[0] + '_nok_eggs_frames.npy', nok_eggs_frames)

    def open_video(self, init, frame_number):

        self.frame_number = frame_number

        if not init:
            self.cap.release()

            if self.show_worm_details.get() == 1:
                self.cap_original.release()
                self.cap_original = cv2.VideoCapture(os.path.join(self.working_path, self.working_assay, self.video))
                if not self.cap_original.isOpened():
                    print("Error can't open video ", os.path.join(self.working_path, self.working_assay, self.video))

        self.cap = cv2.VideoCapture(os.path.join(self.videos_path, self.video))
        self.video_number = 0

        if self.cap.isOpened():

            trozos = self.video.split('.')

            try:
                self.video_number = int(trozos[0])
            except ValueError:
                self.video_number = 0

            self.eggs_ok_listbox_previous = []
            self.eggs_nok_listbox_previous = []

            if os.path.isfile(self.videos_path + '/' + trozos[0] + '_track_eggs_frames.npy'):
                self.track_eggs_frames = list(np.load(self.videos_path + '/' + trozos[0] + '_track_eggs_frames.npy'))
            if os.path.isfile(self.videos_path + '/' + trozos[0] + '_ok_eggs_frames.npy'):
                self.ok_eggs_frames = list(np.load(self.videos_path + '/' + trozos[0] + '_ok_eggs_frames.npy'))
            if os.path.isfile(self.videos_path + '/' + trozos[0] + '_nok_eggs_frames.npy'):
                self.nok_eggs_frames = list(np.load(self.videos_path + '/' + trozos[0] + '_nok_eggs_frames.npy'))
            if os.path.isfile(self.videos_path + '/' + trozos[0] + '_metadata_eggs_frames.csv'):
                self.frames_poses = pd.read_csv(self.videos_path + '/' + trozos[0] + '_metadata_eggs_frames.csv')

            # Elimina los elementos emparejados de las listas nok_eggs_frames y track_eggs_frames
            for item in self.ok_eggs_frames:
                if item[0] in self.nok_eggs_frames:
                    self.nok_eggs_frames.remove(item[0])
                if item[1] in self.track_eggs_frames:
                    self.track_eggs_frames.remove(item[1])

            # Elimina los elementos de la lista track_eggs_frames que están en nok_eggs_frames
            for item in self.nok_eggs_frames:
                if item in self.track_eggs_frames:
                    self.track_eggs_frames.remove(item)

            # Fusiona y ordena las listas nok_eggs_frames y track_eggs_frames
            self.nok_eggs_frames = self.nok_eggs_frames + self.track_eggs_frames
            self.nok_eggs_frames.sort()

            # self.tabla_poses = np.array([])
            # if os.path.isfile(self.videos_path + '/' + trozos[0] + '_poses.npy'):
            #     self.tabla_poses = np.load(self.videos_path + '/' + trozos[0] + '_poses.npy')
            #     # print('pose:', self.tabla_poses[self.frame_number])

            self.img = np.zeros((100, 100, 3), np.uint8)
            if os.path.isfile(self.videos_path + '/' + trozos[0] + '_img_result_tracking.bmp'):
                self.img = cv2.imread(self.videos_path + '/' + trozos[0] + '_img_result_tracking.bmp')

            self.tabla_poses = [[0,0]] * 18000 # 18000 Frames per video
            if os.path.isfile(self.videos_path + '/' + trozos[0] + '_poses.npy'):
                self.tabla_poses = np.load(self.videos_path + '/' + trozos[0] + '_poses.npy')

            self.imgs_pair[0] = np.ones((128, 128, 3), np.uint8) * 255
            self.imgs_pair[1] = np.ones((128, 128, 3), np.uint8) * 255

            if not init:
                self.video_label.config(text="Video: " + self.video)
                self.folder_label.config(text="Selected Assay: "+self.videos_path.split('/')[-1])

                self.eggs_nok_listbox.delete(0, tk.END)
                for item in self.nok_eggs_frames:
                    self.eggs_nok_listbox.insert(tk.END, item)

                self.eggs_ok_listbox.delete(0, tk.END)
                for item in self.ok_eggs_frames:
                    #self.eggs_ok_listbox.insert(tk.END, str(item[0]) + "." + str(item[1]))
                    if item[1] == -1:
                        self.eggs_ok_listbox.insert(tk.END, str(item[0]) + ".0")
                    else:
                        self.eggs_ok_listbox.insert(tk.END, str(item[0]) + "." + str(item[1]))

                self.root.update()

            if not self.playing_video:
                self.play_video()

        return self.cap.isOpened()

    def select_video(self, event):
        # Obtener el índice del elemento seleccionado
        self.videos_listbox.selection_clear(0, tk.END)
        self.videos_listbox.selection_set(self.videos_listbox.nearest(event.y))
        self.videos_listbox.activate(self.videos_listbox.nearest(event.y))
        index_video = self.videos_listbox.curselection()

        if index_video:
            # Obtener el valor del elemento seleccionado
            self.video = self.videos_listbox.get(index_video)
            self.index_video = index_video[0]
            #print("Indice seleccionado:", self.index_video)
            print("Selected Video:", self.video)

            if self.open_video(False, 0):
                self.inc = 1
            else:
                print('Error: this video can not be opened!')
                messagebox.showerror("Selected Video: "+self.video, 'Error: this video can not be opened!')

    def process_assays(self):
        for working_assay in self.working_assays:
            originals_videos = self.read_videos_from_folder(os.path.join(self.working_path, working_assay))
            # Para lanzar todos los ensayos en paralelo
            x = threading.Thread(target=lib.thread_process_assay,
                                 args=(self.working_path, working_assay, originals_videos,),
                                 daemon=True)
            x.start()
            ## Para lanzar los ensayos en serie
            #lib.thread_process_assay(self.working_path, working_assay, originals_videos)

            self.set_originals_path(self.working_path, self.working_assay, False)

    def process_videos(self):
        originals_path = os.path.join(self.working_path, self.working_assay)
        for originals_video in self.originals_videos:
            name_video = originals_video.split('.')[0]
            if not lib.is_process_init(originals_path, name_video):
                ## Para lanzar todos los vídeos de un ensayo en paralelo
                # x = threading.Thread(target=lib.thread_process_video,
                #                      args=(originals_path + '/', name_video, True,),
                #                      daemon=True)
                # x.start()
                ## Para lanzar los vídeos de un ensayo en serie
                lib.thread_process_video(originals_path + '/', name_video, True)

                self.set_originals_path(self.working_path, self.working_assay, False)
            else:
                path_name_video = os.path.join(originals_path, name_video)
                print('--------------------------path:', path_name_video)
                print('This video has been processed. Delete the processed folder if you want to process it again...')

    def process_video(self, event):
        # Obtener el índice del elemento seleccionado
        self.originals_videos_listbox.selection_clear(0, tk.END)
        self.originals_videos_listbox.selection_set(self.originals_videos_listbox.nearest(event.y))
        self.originals_videos_listbox.activate(self.originals_videos_listbox.nearest(event.y))
        index_video = self.originals_videos_listbox.curselection()

        if index_video:
            # Obtener el valor del elemento seleccionado
            originals_video = self.originals_videos_listbox.get(index_video)
            print("Processing Original Video:", originals_video)

            originals_path = os.path.join(self.working_path, self.working_assay)
            name_video = originals_video.split('.')[0]

            if not lib.is_process_init(originals_path, name_video):

                if messagebox.askokcancel('¡Cuidado!','¿Quieres procesar el video ' + originals_video + '?'):

                    #frame_items = lib.video_process(originals_path + '/', originals_video.split('.')[0], True)
                    x = threading.Thread(target=lib.thread_process_video, args=(originals_path + '/', name_video, True,), daemon=True)
                    x.start()

                    self.set_originals_path(self.working_path, self.working_assay, False)
            else:
                path_name_video = os.path.join(originals_path, name_video)
                print('--------------------------path:', path_name_video)
                print('Ya está procesado...')

    def waithere(self):
        pass

    def play_video(self):

        if not self.playing_video:
            self.playing_video = True

        self.inc = 1
        # self.inc_entry.delete(0, tk.END)
        # self.inc_entry.insert(0, str(self.inc))

        while True:
        #while self.cap.isOpened():

            start_time = time.time()  # Tiempo de inicio

            if self.cap.isOpened():
                if (self.frame_number + self.inc) < 0:
                    if self.index_video > 0:
                        #frame_number = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) + self.frame_number + self.inc) # Problema si el último vídeo tiene una cantidad de frames diferente
                        frame_number = int(18000 + self.frame_number + self.inc) # todo: cambiar 18000 si cambia la cantidad de frames por vídeo
                        self.index_video = self.index_video - 1
                        self.video = self.videos[self.index_video]
                        if not self.open_video(False, frame_number):
                            print("Error al abrir el video:", self.videos_path + '/' + self.video)
                            continue

                    else:
                        self.frame_number = 0
                elif (self.frame_number + self.inc) >= self.cap.get(cv2.CAP_PROP_FRAME_COUNT):
                    if self.index_video < len(self.videos)-1:
                        frame_number = int(self.frame_number + self.inc - self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        self.index_video = self.index_video + 1
                        self.video = self.videos[self.index_video]
                        if not self.open_video(False, frame_number):
                            print("Error al abrir el video:", self.videos_path + '/' + self.video)
                            continue

                    else:
                        self.frame_number = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)-1)
                else:
                    self.frame_number = self.frame_number + self.inc

                if self.inc != 1:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
                ret, frame = self.cap.read()

                if not ret:
                    print("Error al intentar leer el frame: ",  self.frame_number," del video:", self.video)
                    break

                frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))-1
                self.frame_label.config(text="Frame: {}".format(frame_number))

                sec = (self.video_number * 12 * 60) + (int(self.frame_number) / 25)
                self.time_label.config(text="Time: " + strfdelta(datetime.timedelta(seconds=sec)))

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # todo:  draw_circle
                if self.mark_egg.get() == 1:
                    worm_pose = self.tabla_poses[self.frame_number]
                    x_ini = max(0, worm_pose[0] - 64)
                    y_ini = max(0, worm_pose[1] - 64)
                    frame = cv2.circle(frame, (self.egg_pose[0]-y_ini, self.egg_pose[1]-x_ini), 10, (255, 0, 0), 1)

                image = cv2.resize(frame, self.size_window)

                image = ImageTk.PhotoImage(image=Image.fromarray(image))
                self.canvas.create_image(0, 0, anchor=tk.NW, image=image)

                image_egg = ImageTk.PhotoImage(image=Image.fromarray(self.imgs_pair[0]))
                self.canvas_egg.create_image(0, 0, anchor=tk.NW, image=image_egg)

                image_track = ImageTk.PhotoImage(image=Image.fromarray(self.imgs_pair[1]))
                self.canvas_track.create_image(0, 0, anchor=tk.NW, image=image_track)

                self.root.update()

                if (self.show_track.get() == 1) or (self.show_worm_details.get() == 1):
                    pose = self.tabla_poses[self.frame_number]
                    x_ini = max(0, pose[0] - 64)
                    x_fin = min(self.img.shape[0], pose[0] + 64)
                    y_ini = max(0, pose[1] - 64)
                    y_fin = min(self.img.shape[1], pose[1] + 64)
                    height = x_fin - x_ini
                    width = y_fin - y_ini

                if self.show_track.get() == 1:
                    alpha = np.ones((height, width), np.uint8) * 0.75
                    cv2.circle(alpha, (int(width / 2), int(height / 2)), 64, 1, -1)
                    img_copy = self.img.copy()
                    img_copy[x_ini:x_fin, y_ini:y_fin, 0] = img_copy[x_ini:x_fin, y_ini:y_fin, 0] * alpha
                    img_copy[x_ini:x_fin, y_ini:y_fin, 1] = img_copy[x_ini:x_fin, y_ini:y_fin, 1] * alpha
                    img_copy[x_ini:x_fin, y_ini:y_fin, 2] = img_copy[x_ini:x_fin, y_ini:y_fin, 2] * alpha
                    cv2.imshow("Track", img_copy)

                if (self.show_worm_details.get() == 1) and self.cap_original.isOpened():
                        if self.inc != 1:
                            self.cap_original.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
                        ret_original, frame_original = self.cap_original.read()
                        img_recortada = frame_original[x_ini:x_fin, y_ini:y_fin,:]
                        cv2.imshow("Worm details", img_recortada)

                end_time = time.time()
                elapsed_time = (end_time - start_time) * 1000

                if self.cap.get(cv2.CAP_PROP_FPS) > 0:
                    delay = int(1000 / (self.cap.get(cv2.CAP_PROP_FPS) * self.speed_factor))
                else:
                    delay = 0
            else:
                end_time = time.time()
                elapsed_time = (end_time - start_time) * 1000
                delay = 40

            if delay > elapsed_time:
                self.root.after(int(delay-elapsed_time), self.waithere())
                #if cv2.waitKey(delay) & 0xFF == ord('q'):
                #    break

    def go_to_frame_Return(self, event):
        self.go_to_frame()

    def go_to_frame(self):
        new_frame = self.frame_entry.get()
        if new_frame.isnumeric():
            self.frame_number = int(new_frame)
            self.inc = 0

    def select_nok_0(self, event):
        # Obtener el índice del elemento seleccionado
        self.eggs_nok_listbox.selection_clear(0, tk.END)
        self.eggs_nok_listbox.selection_set(self.eggs_nok_listbox.nearest(event.y))
        self.eggs_nok_listbox.activate(self.eggs_nok_listbox.nearest(event.y))
        index_frame = self.eggs_nok_listbox.curselection()
        self.select_nok(index_frame)

    def select_nok_Up(self, event):
        index_frame = self.eggs_nok_listbox.curselection()
        if index_frame:
            if (index_frame[0] - 1) >= 0:
                index_frame = (index_frame[0]-1,)
                self.select_nok(index_frame)

    def select_nok_Down(self, event):
        index_frame = self.eggs_nok_listbox.curselection()
        if index_frame:
            if (index_frame[0] + 1) < self.eggs_nok_listbox.size():
                index_frame = (index_frame[0]+1,)
                self.select_nok(index_frame)

    def select_nok(self, index_frame):

        if index_frame:           # Obtener el valor del elemento seleccionado
            frames = self.eggs_nok_listbox.get(index_frame).split('.')
            self.frame_number = int(self.eggs_nok_listbox.get(index_frame))
            self.inc = 0

            video_name = self.video.split('.')[0]
            imgs_folder = self.videos_path + "/" + video_name + '_imgs/'

            self.edit_layedEgg_entry.delete(0, tk.END)
            self.edit_trackedEgg_entry.delete(0, tk.END)

            for index1, frame in enumerate(frames):
                frame_number = int(frames[index1])
                self.imgs_pair[index1] = np.ones((128, 128, 3), np.uint8)*255
                img_subname = video_name + '_' + str(frame_number) + '_'
                for filename in os.listdir(imgs_folder):
                    if img_subname in filename:
                        img = cv2.imread(imgs_folder + filename)[..., ::-1]
                        max_side = max(img.shape[0], img.shape[1])
                        scale = 128.0 / max_side
                        t0 = filename.split('.')[0]
                        t1 = t0.split('_')[2]
                        t2 = t1.split('x')
                        self.egg_pose = (int(t2[1]), int(t2[0]))
                        if '_eggs' in filename:
                            self.imgs_pair[1] = cv2.resize(img, (int(img.shape[1]*scale), int(img.shape[0]*scale)))
                            self.edit_trackedEgg_entry.insert(0, str(frame_number))
                        else:
                            self.imgs_pair[0] = cv2.resize(img, (int(img.shape[1]*scale), int(img.shape[0]*scale)))
                            self.imgs_pair[1] = np.ones((128, 128, 3), np.uint8)*255
                            self.edit_layedEgg_entry.insert(0, str(frame_number))
                        break

    def select_ok_0(self, event):
        # Obtener el índice del elemento seleccionado
        self.eggs_ok_listbox.selection_clear(0, tk.END)
        self.eggs_ok_listbox.selection_set(self.eggs_ok_listbox.nearest(event.y))
        self.eggs_ok_listbox.activate(self.eggs_ok_listbox.nearest(event.y))
        index_frame = self.eggs_ok_listbox.curselection()
        self.select_ok(index_frame, 0)

    def select_ok_1(self, event):
        # Obtener el índice del elemento seleccionado
        self.eggs_ok_listbox.selection_clear(0, tk.END)
        self.eggs_ok_listbox.selection_set(self.eggs_ok_listbox.nearest(event.y))
        self.eggs_ok_listbox.activate(self.eggs_ok_listbox.nearest(event.y))
        index_frame = self.eggs_ok_listbox.curselection()
        self.select_ok(index_frame, 1)

    def select_ok_Up(self, event):
        index_frame = self.eggs_ok_listbox.curselection()
        if index_frame:
            if (index_frame[0] - 1) >= 0:
                index_frame = (index_frame[0]-1,)
                self.select_ok(index_frame, 0)

    def select_ok_Down(self, event):
        index_frame = self.eggs_ok_listbox.curselection()
        if index_frame:
            if (index_frame[0] + 1) < self.eggs_ok_listbox.size():
                index_frame = (index_frame[0]+1,)
                self.select_ok(index_frame, 0)

    def select_ok(self, index_frame, index):

        if index_frame:
            # Obtener el valor del elemento seleccionado
            frames = self.eggs_ok_listbox.get(index_frame).split('.')
            self.frame_number = int(frames[index])
            self.inc = 0

            video_name = self.video.split('.')[0]
            imgs_folder = self.videos_path + "/" + video_name + '_imgs/'

            self.edit_layedEgg_entry.delete(0, tk.END)
            self.edit_trackedEgg_entry.delete(0, tk.END)

            for index1 in range(2):
                frame_number = int(frames[index1])
                self.imgs_pair[index1] = np.ones((128, 128, 3), np.uint8)*255
                img_subname = video_name + '_' + str(frame_number) + '_'
                for filename in os.listdir(imgs_folder):
                    if img_subname in filename:
                        img = cv2.imread(imgs_folder+filename)[..., ::-1]
                        max_side = max(img.shape[0], img.shape[1])
                        scale = 128.0 / max_side
                        if '_eggs' in filename:
                            if index1 == 1:
                                self.imgs_pair[1] = cv2.resize(img, (int(img.shape[1]*scale), int(img.shape[0]*scale)))
                                self.edit_trackedEgg_entry.insert(0, str(frame_number))
                        else:
                            if index1 == 0:
                                self.imgs_pair[0] = cv2.resize(img, (int(img.shape[1]*scale), int(img.shape[0]*scale)))
                                self.imgs_pair[1] = np.ones((128, 128, 3), np.uint8)*255
                                self.edit_layedEgg_entry.insert(0, str(frame_number))
                        break

                if index1 == 0:
                    res = self.frames_poses.loc[self.frames_poses['frame_num'] == frame_number]
                    if len(res) == 1:
                        self.egg_pose = (res['cx'].values[0], res['cy'].values[0])

    def prev_frame_Left(self, event):
        self.prev_frame()

    def prev_frame(self):
        self.frame_number = self.frame_number - 1
        self.inc = 0

    def pause_video(self):
        self.inc = 0

    def next_frame_Right(self, event):
        self.next_frame()

    def next_frame(self):
        self.frame_number = self.frame_number + 1
        self.inc = 0

    def forward_video_lento(self, event):
        self.inc = 1

    def backward_video_lento(self, event):
        self.inc = -1

    def forward_video(self, event):
        self.inc = int(self.inc_entry.get())

    def backward_video(self, event):
        self.inc = -int(self.inc_entry.get())

    def show_mark_egg(self):
        min_dist = 9999999
        frame_number = self.frame_number
        for frame_pose in self.frames_poses['frame_num']:
            dist = abs(self.frame_number - frame_pose)
            if dist < min_dist:
                min_dist = dist
                frame_number = frame_pose

        res = self.frames_poses.loc[self.frames_poses['frame_num'] == frame_number]
        if len(res) == 1:
            self.egg_pose = (res['cx'].values[0], res['cy'].values[0])
        else:
            self.egg_pose = (0, 0)

    def show_details(self):
        if self.show_worm_details.get() == 1:
            originals_path = os.path.join(self.working_path, self.working_assay)
            self.cap_original = cv2.VideoCapture( originals_path + '/'  + self.video)
            #cv2.namedWindow("Worm details", cv2.WINDOW_NORMAL)
            #cv2.resizeWindow('Worm details', int(self.img.shape[0] / 5), int(self.img.shape[1] / 5))
            cv2.namedWindow("Worm details", cv2.WINDOW_KEEPRATIO)
            self.cap_original.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
        else:
            cv2.destroyWindow("Worm details")

    def show_trajectory(self):
        if self.show_track.get() == 1:
            #cv2.namedWindow("Track", cv2.WINDOW_NORMAL)
            #cv2.resizeWindow('Track', int(self.img.shape[0] / 3), int(self.img.shape[1] / 3))
            cv2.namedWindow("Track", cv2.WINDOW_KEEPRATIO)
            cv2.setMouseCallback('Track', self.track_mouse_callback)
        else:
            cv2.destroyWindow("Track")

    def move_selected_item_OK(self):
        selected_index = self.eggs_nok_listbox.curselection()
        if selected_index:
            selected_item = self.eggs_nok_listbox.get(selected_index[0])

            video_name = self.video.split('.')[0]
            imgs_folder = self.videos_path + "/" + video_name + '_imgs/'
            frame_number = int(selected_item)
            img_subname = video_name + '_' + str(frame_number) + '_'
            for filename in os.listdir(imgs_folder):
                if img_subname in filename:
                    if '_eggs' in filename:
                        selected_item = selected_item + "." + selected_item
                    else:
                        selected_item = selected_item + ".0"
                    break

            actual_ok_list = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
            self.eggs_ok_listbox_previous.append(actual_ok_list)
            self.eggs_ok_listbox.insert(tk.END, selected_item)

            actual_nok_list = list(self.eggs_nok_listbox.get(0, self.eggs_nok_listbox.size() - 1))
            self.eggs_nok_listbox_previous.append(actual_nok_list)
            self.eggs_nok_listbox.delete(selected_index[0])

            # Order items
            actual_list = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
            actual_list_tuples = [item.split('.') for item in actual_list]
            actual_list_tuples.sort(key=lambda x: int(x[0]))
            actual_list = [item[0] + '.' + item[1] for item in actual_list_tuples]
            #actual_list = [item[0].zfill(5)+'.'+item[1].zfill(5) for item in actual_list_tuples]
            self.eggs_ok_listbox.delete(0, tk.END)
            for item in actual_list:
                self.eggs_ok_listbox.insert(tk.END, item)

            self.save_results()

    def delete_item_OK(self):
        selected_index = self.eggs_ok_listbox.curselection()
        if selected_index:
            actual_ok_list = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
            self.eggs_ok_listbox_previous.append(actual_ok_list)
            self.eggs_ok_listbox.delete(selected_index[0])
            self.save_results_ok()

    def edit_item_layedEgg_Return(self, event):
        self.edit_item_trackedEgg()

    def edit_item_layedEgg(self):

        new_frame = self.edit_layedEgg_entry.get()

        selected_index = self.eggs_ok_listbox.curselection()
        if selected_index and new_frame.isnumeric():
            actual_ok_list = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
            self.eggs_ok_listbox_previous.append(actual_ok_list)
            frames_str = self.eggs_ok_listbox.get(selected_index[0])
            self.eggs_ok_listbox.delete(selected_index[0])
            trozos = frames_str.split('.')
            new_frames_str = new_frame + '.' + trozos[1]
            self.eggs_ok_listbox.insert(selected_index[0], new_frames_str)

            # Order items
            actual_list = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
            actual_list_tuples = [item.split('.') for item in actual_list]
            actual_list_tuples.sort(key=lambda x: int(x[0]))
            actual_list = [item[0] + '.' + item[1] for item in actual_list_tuples]
            self.eggs_ok_listbox.delete(0, tk.END)
            for item in actual_list:
                self.eggs_ok_listbox.insert(tk.END, item)

            self.save_results_ok()

        # selected_index = self.eggs_nok_listbox.curselection()
        # if selected_index:
        #     actual_nok_list = list(self.eggs_nok_listbox.get(0, self.eggs_nok_listbox.size() - 1))
        #     self.eggs_nok_listbox_previous.append(actual_nok_list)
        #     #frames_str = self.eggs_nok_listbox.get(selected_index[0])
        #     self.eggs_nok_listbox.delete(selected_index[0])
        #     self.eggs_nok_listbox.insert(selected_index[0], new_frame)
        #     self.save_results_nok()

    def edit_item_trackedEgg_Return(self, event):
        self.edit_item_trackedEgg()

    def edit_item_trackedEgg(self):

        new_frame = self.edit_trackedEgg_entry.get()

        selected_index = self.eggs_ok_listbox.curselection()
        if selected_index and new_frame.isnumeric():
            actual_ok_list = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
            self.eggs_ok_listbox_previous.append(actual_ok_list)
            frames_str = self.eggs_ok_listbox.get(selected_index[0])
            self.eggs_ok_listbox.delete(selected_index[0])
            trozos = frames_str.split('.')
            new_frames_str = trozos[0] + '.' + new_frame
            self.eggs_ok_listbox.insert(selected_index[0], new_frames_str)
            self.save_results_ok()

        # selected_index = self.eggs_nok_listbox.curselection()
        # if selected_index:
        #     actual_nok_list = list(self.eggs_nok_listbox.get(0, self.eggs_nok_listbox.size() - 1))
        #     self.eggs_nok_listbox_previous.append(actual_nok_list)
        #     #frames_str = self.eggs_nok_listbox.get(selected_index[0])
        #     self.eggs_nok_listbox.delete(selected_index[0])
        #     self.eggs_nok_listbox.insert(selected_index[0], new_frame)
        #     self.save_results_nok()

    def undo_item_NOK(self):
        if len(self.eggs_nok_listbox_previous) > 0:
            actual_nok_list = self.eggs_nok_listbox_previous.pop(-1)
            self.eggs_nok_listbox.delete(0, tk.END)
            for item in actual_nok_list:
                self.eggs_nok_listbox.insert(tk.END, str(item))
            self.save_results_nok()

    def delete_item_NOK(self):
        selected_index = self.eggs_nok_listbox.curselection()
        if selected_index:
            actual_nok_list = list(self.eggs_nok_listbox.get(0, self.eggs_nok_listbox.size() - 1))

            # Si está, borra frame de self.track_eggs_frames
            frame_str = self.eggs_nok_listbox.get(selected_index[0])
            new_track_eggs_frames = []
            for item in self.track_eggs_frames:
                if not item == int(frame_str):
                    new_track_eggs_frames.append(item)
            self.track_eggs_frames = new_track_eggs_frames
            path_name_video = os.path.join(self.videos_path, self.video.split('.')[0])
            np.save(path_name_video + '_track_eggs_frames.npy', new_track_eggs_frames)

            self.eggs_nok_listbox_previous.append(actual_nok_list)
            self.eggs_nok_listbox.delete(selected_index[0])
            self.save_results_nok()

    def duplicate_item_OK(self):
        selected_index = self.eggs_ok_listbox.curselection()
        if selected_index:
            actual_ok_list = list(self.eggs_ok_listbox.get(0, self.eggs_ok_listbox.size() - 1))
            self.eggs_ok_listbox_previous.append(actual_ok_list)
            selected_item = self.eggs_ok_listbox.get(selected_index[0])
            self.eggs_ok_listbox.insert(selected_index[0]+1, selected_item)
            self.save_results_ok()

    def undo_item_OK(self):
        if len(self.eggs_ok_listbox_previous) > 0:
            actual_ok_list = self.eggs_ok_listbox_previous.pop(-1)
            self.eggs_ok_listbox.delete(0, tk.END)
            for item in actual_ok_list:
                self.eggs_ok_listbox.insert(tk.END, str(item))
            self.save_results_ok()

    def select_time_frame(self, event):
        seleccion = self.time_frames_listbox.curselection()
        if seleccion:
            indice = seleccion[0]
            self.frame_number = int(self.time_frames_listbox.get(indice))
            print("Selected frame:", self.frame_number)
            self.ventana_flotante.destroy()
            self.exist_ventana_flotante = False
            self.inc = 0

    def update_ventana_flotante(self, frames):
        if not self.exist_ventana_flotante:
            self.exist_ventana_flotante = True
            self.ventana_flotante = tk.Toplevel(self.root)
            self.ventana_flotante.title("Select Frame")
            self.ventana_flotante.geometry("400x200")

            self.time_frames_listbox = tk.Listbox(self.ventana_flotante, exportselection=False)
            self.time_frames_listbox.pack(pady=10)

            # Vincular evento de clic de ratón a la función
            self.time_frames_listbox.bind('<Button-1>', self.select_time_frame)

        self.time_frames_listbox.delete(0, tk.END)
        for elemento in frames:
            self.time_frames_listbox.insert(tk.END, elemento)
        self.ventana_flotante.focus()
        #self.ventana_flotante.grab_set()

    def track_mouse_callback(self,event,x,y,flags,param):
        #if event == cv2.EVENT_LBUTTONUP:
        if event == cv2.EVENT_LBUTTONDBLCLK:
            #self.pixel = (x, y)
            #pose = self.tabla_poses[self.frame_number]
            #print(self.pixel, pose)
            distances = np.full(len(self.tabla_poses), 101)
            dist_min = 100
            for frame, pose in enumerate(self.tabla_poses):
                d1 = y-pose[0]
                d2 = x-pose[1]
                distances[frame] = math.sqrt((d1*d1)+(d2*d2))
                if distances[frame] <= dist_min:
                    dist_min = distances[frame]

            frames = list(np.where(distances == dist_min))[0]

            if len(frames) > 0:
                self.frame_number = int(frames[0])
                self.inc = 0
                self.update_ventana_flotante(frames)

def main():
    #videos_path = '/home/antonio/Descargas/egg_laying_new_v4_9/Gusano 2'
    #player = VideoPlayer(videos_path)
    if os.path.exists("rutas.txt"):
        print("El archivo 'rutas.txt' existe.")
        with open("rutas.txt", "r") as f:
            rutas = [line.strip() for line in f.readlines()]
            if len(rutas) >= 1:
                working_path = rutas[0]
                padre = os.path.dirname(working_path)
                checked_path = os.path.join(padre, "egg_laying_new")
            else:
                working_path = '/' 
                checked_path = '/'
    else:
        working_path = '/' 
        checked_path = '/'
    
    #working_path = '/home/antonio/Descargas/egg_laying/' # carpeta de trabajo donde están los videos originales -> la carpeta de resultados se define de manera automática añadiendo _new a egg_laying en lib.process_in_detail
    #checked_path = '/home/antonio/Descargas/egg_laying_new/' # carpeta de chequeo, que puede ser indepenciente de la carpeta originals_path
    working_assay = '' #'Gusano 2'
    player = VideoPlayer(working_path, checked_path, working_assay)
    player.root.mainloop()

if __name__ == "__main__":
    main()

