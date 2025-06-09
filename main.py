import flet as ft
import json
import os
import shutil
import pygame
import time
from threading import Thread

def main(page: ft.Page):
    # Инициализация pygame для аудио
    pygame.mixer.init()
    
    page.bgcolor = "#393c42"
    page.title = "FurryMusic"

    class SongStorage:
        def __init__(self):
            try:
                with open("songs.json", "r") as f:
                    self.songs = json.load(f)
            except:
                self.songs = []
        
        def save(self):
            with open("songs.json", "w") as f:
                json.dump(self.songs, f)
        
        def add_song(self, title, file_path=None):
            self.songs.append({
                "title": title, 
                "icon": "ALBUM", 
                "file_path": file_path,
                "filename": os.path.basename(file_path)
            })
            self.save()

        def remove_song(self, index):
            song = self.songs[index]
            file_path = song["file_path"]
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            self.songs.pop(index)
            self.save()

    song_storage = SongStorage()
    current_song_index = 0
    is_playing = False
    current_song = None

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            os.makedirs("music", exist_ok=True)
            for file in e.files:
                if file.name.endswith('.mp3'):
                    new_path = os.path.join("music", file.name)
                    shutil.copy(file.path, new_path)
                    
                    song_storage.add_song(
                        title=os.path.splitext(file.name)[0],
                        file_path=new_path
                    )
            refresh_playlist()

    file_picker.on_result = pick_files_result

    def play_audio(e=None):
        nonlocal is_playing, current_song
        
        if not song_storage.songs:
            return
            
        song = song_storage.songs[current_song_index]
        
        if is_playing:
            pygame.mixer.music.pause()
            play_button.icon = ft.Icons.PLAY_ARROW
            is_playing = False
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.load(song["file_path"])
                pygame.mixer.music.play()
            
            play_button.icon = ft.Icons.PAUSE
            current_song_title.value = f"▶ {song['title']}"
            is_playing = True
            
            # Запускаем поток для отслеживания конца песни
            Thread(target=check_music_end, daemon=True).start()
        
        page.update()

    def check_music_end():
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        if is_playing:
            next_song()

    def stop_audio(e=None):
        nonlocal is_playing
        pygame.mixer.music.stop()
        play_button.icon = ft.Icons.PLAY_ARROW
        is_playing = False
        if song_storage.songs:
            current_song_title.value = song_storage.songs[current_song_index]["title"]
        page.update()

    def next_song(e=None):
        nonlocal current_song_index, is_playing
        
        if not song_storage.songs:
            return
            
        if current_song_index < len(song_storage.songs) - 1:
            current_song_index += 1
        else:
            current_song_index = 0
            
        song = song_storage.songs[current_song_index]
        current_song_title.value = song["title"]
        
        if is_playing:
            pygame.mixer.music.load(song["file_path"])
            pygame.mixer.music.play()
            Thread(target=check_music_end, daemon=True).start()
        
        page.update()

    # Элементы интерфейса
    current_song_title = ft.Text("Выберите песню", size=16)
    
    play_button = ft.IconButton(
        icon=ft.Icons.PLAY_ARROW,
        icon_size=40,
        icon_color=ft.Colors.GREEN,
        on_click=play_audio
    )
    
    stop_button = ft.IconButton(
        icon=ft.Icons.STOP,
        icon_size=40,
        icon_color=ft.Colors.RED,
        on_click=stop_audio
    )
    
    next_button = ft.IconButton(
        icon=ft.Icons.SKIP_NEXT,
        icon_size=40,
        on_click=next_song
    )

    def playlist():
        song_list = ft.ListView(
            spacing=10,
            padding=ft.padding.symmetric(vertical=10),
            expand=True
        )

        for idx, song in enumerate(song_storage.songs):
            song_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        width=500,
                        content=ft.Column(
                            controls=[
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.ALBUM),
                                    title=ft.Text(song["title"]),
                                    on_click=lambda e, idx=idx: select_song(idx),
                                    trailing=ft.PopupMenuButton(
                                        icon=ft.Icons.MORE_VERT,
                                        items=[
                                            ft.PopupMenuItem(
                                                text="Удалить",
                                                on_click=lambda e, idx=idx: delete_song(e, idx)
                                            )
                                        ],
                                    ),
                                )
                            ]
                        )
                    )
                )
            )

        return ft.Column(
            controls=[
                ft.Container(
                    content=song_list,
                    height=page.height * 0.8 if page.height else 400,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def select_song(index):
        nonlocal current_song_index, is_playing
        current_song_index = index
        song = song_storage.songs[index]
        current_song_title.value = song["title"]
        
        if is_playing:
            pygame.mixer.music.load(song["file_path"])
            pygame.mixer.music.play()
            Thread(target=check_music_end, daemon=True).start()
        
        change_page(1)  # Переключаем на вкладку плеера
        page.update()

    def refresh_playlist():
        page.controls.clear()
        page.appbar = bar("Плейлист")
        page.add(playlist())
        page.update()

    def add_song(e):
        file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=["mp3"],
            dialog_title="Выберите MP3 файлы"
        )
    
    def delete_song(e, index):
        song_storage.remove_song(index)
        refresh_playlist()
    
    def play():
        return ft.Column(
            controls=[
                ft.Text("Сейчас играет:", size=20),
                current_song_title,
                ft.Row(
                    controls=[
                        play_button,
                        stop_button, 
                        next_button
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def profile():
        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def bar(t_text):
        return ft.AppBar(
            title=ft.Text(t_text),
            center_title=True,
            bgcolor="#222325",
            automatically_imply_leading=False,
            shape=ft.RoundedRectangleBorder(
                radius=ft.border_radius.vertical(bottom=20, top=20)
            )   
        )
    
    def change_page(index):
        page.controls.clear()

        if index == 0:
            page.appbar = bar("Плейлист")
            page.add(playlist())
        elif index == 1:
            page.appbar = bar("Плеер")
            page.add(play())
        
        page.update()

    # Нижняя панель навигации
    page.bottom_appbar = ft.BottomAppBar(
        bgcolor="#393c42",
        shape=ft.NotchShape.CIRCULAR,
        content=ft.Container(
            height=60,
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.PLAYLIST_PLAY, 
                        icon_color=ft.Colors.WHITE, 
                        on_click=lambda e: change_page(0)
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.PLAY_CIRCLE, 
                        icon_color=ft.Colors.WHITE, 
                        on_click=lambda e: change_page(1)
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.PLAYLIST_ADD_CIRCLE_ROUNDED, 
                        icon_color=ft.Colors.WHITE, 
                        on_click=add_song
                    ),
                ]
            ),
            padding=ft.padding.symmetric(vertical=1, horizontal=20),
            border_radius=15,
            bgcolor="#222325",
        ),
    )
    
    # Начальная страница
    page.appbar = bar("Плеер")
    page.add(play())

# Убедитесь, что установлены зависимости:
# pip install flet pygame
ft.app(target=main)