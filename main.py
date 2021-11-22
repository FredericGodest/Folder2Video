"""
This is the main Module where everything is stored.

"""

import os
from datetime import datetime
import pandas as pd
from moviepy.editor import *
import librosa
import difflib

diff = difflib.Differ()

def find_paths() -> str:
    """
    This function is scanning all the files and folders in the current directory.
    It detected the folders with the maximum number of files.
    From this folders it will find the audio file.

    :return: audio file name and the main folder path.
    """
    print("Folders Scan")
    nb_file_mem = 0
    for root, dirs, files in os.walk(".", topdown=False):
        for dir in dirs:
            for root, dirs, files in os.walk(dir, topdown=False):
                if len(files) >= nb_file_mem:
                    nb_file_mem = len(files)
                    main_path = os.path.join(".",dir)


    for root, dirs, files in os.walk(main_path, topdown=False):
        for file in files:
            if ".mp3" in file:
                audio_file = file

    print(f"Detected folder = {main_path}")
    print(f"Detected audio file = {audio_file}")
    print("Done")
    print("")

    return audio_file, main_path

def Find_Tempo(path: str) -> float:
    """
    Thanks to Librosa library we can determine the tempo of a given song.
    This function is using this Librosa module and it determine the frame duration for the video.

    :param path: path of the audio file.
    :return: frame duration of the video frame.
    """
    print("Tempo detection")
    snd, sr = librosa.load(path, duration=10)
    tempo, _ = librosa.beat.beat_track(y=snd, sr=sr)
    frame_duration = 60 / tempo
    print(f"tempo = {tempo} bpm")

    print("Done")
    print("")
    return frame_duration

def Create_DataFrame(dir: str) -> dict:
    """
    This function is scapping all the files with pictures or video extension.
    Then

    :param dir: Path to tge folder.
    :return: Pandas dataframe.
    """
    print("Folder scrapping and filtering")
    entries = os.listdir(dir)
    FILE_NAME = []
    CREATION_DATE = []
    extention = [".jpeg", ".png", ".mov"]

    for file in entries:
        for ext in extention:
            if ext in file:
                file_path = os.path.join(dir, file)
                timestamp = os.stat(file_path).st_mtime
                date = datetime.fromtimestamp(timestamp).strftime("%d/%m/%y")
                FILE_NAME.append(file)
                CREATION_DATE.append(date)

    d = {
        "file_name": FILE_NAME,
        "creation_date": CREATION_DATE
    }
    df = pd.DataFrame(data=d)
    df['creation_date'] = pd.to_datetime(df['creation_date'])


    df["order"] = df["file_name"]
    for rep in extention:
        df["order"] = df["order"].str.replace(rep, "", regex=True)

    a = df["order"][1].split(" ")
    b = df["order"][0].split(" ")
    root_word = list(diff.compare(a, b))[0]
    root_word = root_word.replace(" ", "") + " - "
    df["order"] = df["order"].str.replace(root_word, "", regex=True)
    df["order"] = df["order"].astype('int64', copy=False)

    print("Done")
    print(" ")

    return df

def Concat_Clip(df: dict, dir: str, frame_duration: float):
    """
    This function is compiling all the files to create a video.

    :param df: Dataframe of the file name to compile
    :param frame_duration: Frame duration of each file to compile
    :return: MoviePy clip
    """
    print("Clips creation")
    file_name_list = df.sort_values(by=["order"])["file_name"].tolist()
    clips = []
    max_height = 720
    nb_file = len(file_name_list)
    print(f"number of file detected : {nb_file}")

    for i in range(nb_file):
        file = os.path.join(dir, file_name_list[i])
        print(file)
        if ".mov" in file:
            clip = VideoFileClip(file, resize_algorithm="bilinear").set_duration(frame_duration * 4)
        else:
            clip = ImageClip(file).set_duration(frame_duration)

        clip = clip.resize(height=max_height)
        clips.append(clip)

    concat_clip = concatenate_videoclips(clips, method="compose")

    print("Done")
    print("")

    return concat_clip

def Audio_and_Save(path: str, concat_clip, output_name: str):
    """
    This function is adding audio to the previous MoviePy clips.
    Then this audio + clip is saved under the name given by the user.

    :param path: path of the working folder
    :param concat_clip: concatened MoviePy clips
    :param output_name: Name of the final movie.
    :return: Saved video file in the working folder.
    """
    print("Compilation")
    new_audioclip = AudioFileClip(path)
    final_clip = concat_clip.set_audio(new_audioclip)
    final_clip.write_videofile(output_name + ".mp4",
                               fps=24,
                               temp_audiofile="tempaudio.m4a",
                               codec="libx264",
                               remove_temp=False,
                               audio_codec='aac')

def main(path, dir, output_name):
    """
    This is the main function that runs every functions.

    :param path: the path of the working folder.
    :param dir: the name of the working directory.
    :param output_name: the name of the final movie
    """
    frame_duration = Find_Tempo(path)
    df = Create_DataFrame(dir)
    concat_clip = Concat_Clip(df, dir, frame_duration)
    Audio_and_Save(path, concat_clip, output_name)

if __name__ == "__main__":
    output_name = str(input("Ouput file name : "))
    audio_file, main_path = find_paths()
    audio_path = os.path.join(main_path, audio_file)
    main(audio_path, main_path, output_name)