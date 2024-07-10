import os
import re
import shutil
from time import sleep
from threading import Thread

import ffmpeg
import requests
from bs4 import BeautifulSoup
from chompjs import parse_js_object
from DownloadKit import DownloadKit
from DownloadKit.mission import Mission
from Bilibili_Parse import BlibiliParse

DataFindError = IndexError
ScriptsLocateError = RuntimeError


class VideoNameInfer:
    def __init__(self, name: str):
        try:
            part = re.findall(r"\d+", name)[0]
        except IndexError:
            self.start_part = ""
            self.end_part = ""
            return
        self.start_part = name[:name.find(part)]
        self.end_part = name[name.rfind(part) + len(part):]
        self.part: str = part

    def get_name(self, id_: int):
        if len(str(id_)) < len(self.part):
            number = "0" * (len(self.part) - len(str(id_))) + str(id_)
        else:
            number = str(id_)

        return f"{self.start_part}{number}{self.end_part}"

    @property
    def num(self) -> int:
        return int(self.part)


class Lesson:
    def __init__(self, lesson_id: int):
        self.lesson_id = lesson_id
        self.lesson_detail = {}
        self.video_list = []
        self.over_count = 0
        self.cbk = lambda x: print(x)

    def load_video_list(self):
        url = "https://www.codinghou.cn/course/coursedetail/" + str(self.lesson_id)
        resp = requests.get(url)

        soup = BeautifulSoup(resp.text, 'html.parser')
        try:
            script = soup.find_all("script")[-1].text
            if len(script) == 0:
                raise DataFindError("错误, 无法获取数据文本")
            data = script[script.find("return"):script.rfind("}(null,") + 1]
        except IndexError:
            raise DataFindError("索引错误: 无法定位数据位置")
        except TypeError:
            raise ScriptsLocateError("网页经过更改, 无法定位元素位置")
        self.lesson_detail = parse_js_object(data)
        self.video_list = self.lesson_detail["data"]["courseList"]["data"]["list"]

    def wait_mission_thread(self, mission: Mission):
        mission.wait()
        self.over_count += 1
        self.cbk(self.over_count / len(self.video_list))

    def download_vip_files(self, output: str):
        kit = DownloadKit(goal_path=output)
        video_ids = []
        infer = None
        offset = 0
        for i in range(len(self.video_list)):
            video = self.video_list[i]
            if len(video["OSScourseVideo"]) > 1:
                infer = VideoNameInfer(video["OSScourseVideo"].split("/")[-1])
                offset = i - infer.num
        for i in range(len(self.video_list)):
            video = self.video_list[i]
            if len(video["OSScourseVideo"]) > 1:
                Thread(target=self.wait_mission_thread,
                       args=(kit.add(video["OSScourseVideo"]),),
                       daemon=True).start()
            else:
                name = infer.get_name(i - offset) if infer else None
                bv = video["courseVideo"].split(r"/")[-1].split("?")[0]
                if not bv:
                    bv = video["courseVideo"].split(r"/")[-2]
                video_ids.append((bv, name))

        for bv, name in video_ids:
            self.download_bili_file(bv, output, name)
            self.over_count += 1
            self.cbk(self.over_count / len(self.video_list))
        kit.wait(show=True)
        self.cbk(0)
        if r"D:/Desktop" in output or r"D:\Desktop" in output:
            new_out = output.replace(r"D:\Desktop", r"D:\esktop").replace(r"D:/Desktop", r"D:/esktop")
            fps = os.listdir(new_out)
            for i in range(len(fps)):
                video = fps[i]
                old_fp = os.path.join(new_out, video)
                new_fp = os.path.join(output, video)
                shutil.move(old_fp, new_fp)
                self.cbk((i + 1) / len(fps))
            shutil.rmtree(new_out)
            try:
                os.removedirs(r"D:\esktop")
            except OSError:
                pass

    def download_bili_file(self, bv: str, output_path: str, name: str):
        biliparser = BlibiliParse(bv)
        try:
            biliparser.start_parse()
        except FileNotFoundError:
            pass
        self.marge_video(biliparser, output_path, name)

    @staticmethod
    def marge_video(pser: BlibiliParse, output_path: str, name: str):
        video_file, audio_file = pser.save_video_audio
        if name is None:
            bv_name = re.sub('[/:*"<>|?]', '', pser.bv_name)
            output_file = os.path.join(output_path, bv_name) + '.mp4'
        else:
            output_file = os.path.join(output_path, name)
        input_video = ffmpeg.input(video_file)
        input_audio = ffmpeg.input(audio_file)
        output = ffmpeg.output(input_video, input_audio, output_file, vcodec='copy', acodec='copy', r=30, y='-y')
        ffmpeg.run(output, cmd='./ffmpeg_/bin/ffmpeg.exe', capture_stderr=True)

        sleep(0.2)
        os.remove(video_file)
        os.remove(audio_file)


def download(num: int, output: str, cbk):
    lesson = Lesson(num)
    lesson.load_video_list()
    lesson.cbk = cbk
    lesson.download_vip_files(output)
