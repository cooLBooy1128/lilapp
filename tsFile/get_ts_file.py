import os
import re
import time

import urllib.request
from functools import partial

from lxml.etree import HTML
from multiprocessing import Pool
import handle_ts_files
from make_sounds import make_sounds

KEYWORD = 'ipx-352'.upper()
# KEYWORD = ''.upper()
PROCNUM = 16


class URLDownloader:
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'}

    def __init__(self, url):
        self.url = url

    def get_response(self):
        req = urllib.request.Request(self.url, headers=self.headers)
        resp = urllib.request.urlopen(req)
        return resp


class FilesDownloader:
    def __init__(self, baseurl, video_id, basedir):
        self.baseurl = baseurl
        self.video_id = video_id
        self.basedir = basedir

    def get_m3u8_file(self):
        filepath = os.path.join(self.basedir, f'{self.video_id}.m3u8')
        if not os.path.exists(filepath):
            url = f'{self.baseurl}{self.video_id}.m3u8'
            resp = URLDownloader(url).get_response()
            if resp.status == 200:
                content = resp.read()
                with open(filepath, 'wb') as f:
                    f.write(content)

    def get_key_file(self, m3u8file_path=None):
        if m3u8file_path is None:
            m3u8file_path = os.path.join(self.basedir, f'{self.video_id}.m3u8')
        m3u8 = handle_ts_files.M3u8FileParser(m3u8file_path)
        uri, _ = m3u8.get_uri_and_iv()
        filepath = os.path.join(self.basedir, uri)
        if not os.path.exists(filepath):
            url = f'{self.baseurl}{uri}'
            resp = URLDownloader(url).get_response()
            if resp.status == 200:
                content = resp.read()
                with open(filepath, 'wb') as f:
                    f.write(content)

    def get_ts_file(self, filename, filepath):
        url = f'{self.baseurl}{filename}'
        resp = URLDownloader(url).get_response()
        if resp.status == 200:
            content = resp.read()
            with open(filepath, 'wb') as f:
                f.write(content)
        else:
            print(f'response status code={resp.status}, {resp.read()}')

    def get_ts_files(self, filenames, ts_dir, exist_filename):
        for filename in filenames:
            if filename not in exist_filename:
                filepath = os.path.join(ts_dir, filename)
                self.get_ts_file(filename, filepath)
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [Pid-{os.getpid()}] Saved {filepath}")
            # else:
            #     print(f'{filename} exists')


def get_baseurl_and_id():
    url = f'https://jable.tv/videos/{KEYWORD}/'
    resp = URLDownloader(url).get_response()
    root = HTML(resp.read()).getroottree()
    text = root.find('//*[@id="site-content"]/div/div/div[1]/section[1]/script[2]').text
    baseurl = re.search("hlsUrl = '(.*?)'", text).group(1).rsplit('/', 1)[0] + '/'
    video_id = re.search("hlsUrl = '(.*?)'", text).group(1).rsplit('/', 1)[1].split('.')[0]
    return baseurl, video_id


def get_index(filenames, length):
    minIndex = int(filenames[0].split('.')[0][length:])
    maxIndex = int(filenames[-1].split('.')[0][length:])
    return minIndex, maxIndex


def get_groups(n, min_index, max_index):
    groups = []
    total = max_index - min_index + 1
    interval = total // n
    for i in range(min_index, max_index + 1, interval):
        if i + interval > max_index + 1:
            groups.append((i, max_index + 1))
        else:
            groups.append((i, i + interval))
    return groups


def count_files(direc):
    total = os.listdir(direc)
    return len([i for i in total if not i.startswith('out')])


def after_download(shutdown=False):
    make_sounds()
    handle_ts_files.main(basedir, ts_dir, video_id, KEYWORD, min_index, max_index)
    if shutdown:
        print('还有60s关机，赶快保存一下！')
        os.system('shutdown -s -t 60')


def main(indexRange, filenames, ts_dir, basedir):
    new_baseurl, new_video_id = get_baseurl_and_id()
    minIndex, maxIndex = indexRange
    exist_filename = set(os.listdir(ts_dir))
    new_fd = FilesDownloader(new_baseurl, new_video_id, basedir)
    new_fd.get_ts_files(filenames[minIndex:maxIndex], ts_dir, exist_filename)


if __name__ == '__main__':
    baseurl, video_id = get_baseurl_and_id()
    basedir = r'D:\Downloads\{}_{}'.format(KEYWORD, video_id)
    if not os.path.exists(basedir):
        os.mkdir(basedir)
    ts_dir = r'{}\{}_{}'.format(basedir, KEYWORD, video_id)
    if not os.path.exists(ts_dir):
        os.mkdir(ts_dir)
    fd = FilesDownloader(baseurl, video_id, basedir)
    fd.get_m3u8_file()
    fd.get_key_file()
    m3u8file = rf'{basedir}\{video_id}.m3u8'
    filenames = handle_ts_files.M3u8FileParser(m3u8file).get_ts_filenames()
    min_index, max_index = get_index(filenames, len(video_id))
    groups = get_groups(PROCNUM, min_index, max_index)
    print('groups:', groups)

    processPool = Pool(PROCNUM)
    while True:
        try:
            processPool.map(partial(main, filenames=filenames, ts_dir=ts_dir, basedir=basedir), groups)
            count = count_files(ts_dir)
            print(f'Download {count}/{max_index - min_index + 1} files, '
                  f'{count / (max_index - min_index + 1):.2%} complete: {KEYWORD}')
            if count >= max_index - min_index + 1:
                break
        except Exception as e:
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [Pid-{os.getpid()}] Error: {e}")
            time.sleep(3)
    after_download()
    # after_download(True)  # 下载完自动关机
