import os
import re
import get_ts_file


class M3u8FileParser:
    def __init__(self, filepath):
        self.filepath = filepath

    def get_uri_and_iv(self):
        # filepath = rf'D:\Downloads\{self.video_id}.m3u8'
        with open(self.filepath) as f:
            for line in f:
                if 'EXT-X-KEY' in line:
                    # line = line.strip()
                    uri = re.search(r'URI="(.*?)"', line).group(1)
                    iv = re.search(r'IV=0x(.*)', line).group(1)
                    return uri, iv

    def get_ts_filenames(self):
        ts_filenames = []
        with open(self.filepath) as f:
            for line in f:
                line = line.strip()
                if line.endswith('.ts'):
                    ts_filenames.append(line)
        return ts_filenames


class KeyFileParser:
    def __init__(self, filepath):
        self.filepath = filepath

    def get_key(self):
        with open(self.filepath, 'rb') as f:
            return f.read().hex()


class TsFilesHandler:
    def __init__(self, basedir, video_id, keyword):
        self.basedir = basedir
        self.video_id = video_id
        self.keyword = keyword

    @staticmethod
    def decrypt_ts_file(filename, key, iv):
        if not os.path.exists(f'out_{filename}.ts'):
            os.system(f'openssl aes-128-cbc -d -in {filename} -out out_{filename} -nosalt -K {key} -iv {iv}')

    def decrypt_ts_files(self, key, iv, start_index=0, end_index=10):
        for i in range(start_index, end_index + 1):
            filename = f'{self.video_id}{i}.ts'
            self.decrypt_ts_file(filename, key, iv)
            if (i + 1) % 100 == 0:
                print(f'handled {i + 1}/{end_index - start_index + 1} files')

    def combine_ts_files(self, start_index=0, end_index=10):
        with open(r'{}\{}_{}-{}.ts'.format(self.basedir, self.keyword, start_index, end_index), 'ab') as w:
            for i in range(start_index, end_index + 1):
                try:
                    with open(f'out_{self.video_id}{i}.ts', 'rb') as r:
                        w.write(r.read())
                except FileNotFoundError as e:
                    print('FileNotFoundError:', e)


def main(basedir, ts_dir, video_id, keyword, start_index, end_index):
    os.chdir(ts_dir)
    m3u8file_path = os.path.join(basedir, f'{video_id}.m3u8')
    m3u8file = M3u8FileParser(m3u8file_path)
    uri, iv = m3u8file.get_uri_and_iv()
    keyfile_path = os.path.join(basedir, uri)
    keyfile = KeyFileParser(keyfile_path)
    key = keyfile.get_key()
    print(f'key = {key}, iv = {iv}')
    if not os.path.exists(r'{}\{}_{}-{}.ts'.format(basedir, keyword, start_index, end_index)):
        ts_handle = TsFilesHandler(basedir, video_id, keyword)
        ts_handle.decrypt_ts_files(key, iv, start_index, end_index)
        ts_handle.combine_ts_files(start_index, end_index)
        print('Handle TS Files Done!')
    else:
        print(r'{}\{}_{}-{}.ts already exists'.format(basedir, keyword, start, end))


if __name__ == '__main__':
    keyword = 'ipx-603'.upper()
    video_id = '12843'
    basedir = rf'D:\Downloads\{keyword}_{video_id}'
    ts_dir = r'{}\{}_{}'.format(basedir, keyword, video_id)
    m3u8file = rf'{basedir}\{video_id}.m3u8'
    filenames = M3u8FileParser(m3u8file).get_ts_filenames()
    start, end = get_ts_file.get_index(filenames, len(video_id))
    end = 10
    main(basedir, ts_dir, video_id, keyword, start, end)
