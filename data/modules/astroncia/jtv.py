'''
Copyright 2021 Astroncia

    This file is part of Astroncia IPTV.

    Astroncia IPTV is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Astroncia IPTV is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Astroncia IPTV.  If not, see <https://www.gnu.org/licenses/>.
'''
import zipfile
import io
import datetime
import struct
from data.modules.astroncia.time import print_with_time

def filetime_to_datetime(time, settings):
    if len(time) == 8:
        filetime = struct.unpack("<Q", time)[0]
        timestamp = filetime / 10
        return round((datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=timestamp)).timestamp() + (3600 * settings["timezone"]))
    else:
        print_with_time("WARNING: broken JTV time detected!")
        return 0

def parse_titles(data, encoding="cp1251"):
    jtv_headers = [b"JTV 3.x TV Program Data\x0a\x0a\x0a", b"JTV 3.x TV Program Data\xa0\xa0\xa0"]
    if data[0:26] not in jtv_headers:
        raise Exception('Invalid JTV format')
    data = data[26:]
    titles = []
    while data:
        title_length = int(struct.unpack('<H', data[0:2])[0])
        data = data[2:]
        title = data[0:title_length].decode(encoding)
        data = data[title_length:]
        titles.append(title)
    return titles

def parse_schedule(data, settings):
    schedules = []
    records_num = struct.unpack('<H', data[0:2])[0]
    data = data[2:]
    i = 0
    while i < records_num:
        i = i + 1
        record = data[0:12]
        data = data[12:]
        schedules.append(filetime_to_datetime(record[2:-2], settings))
    return schedules

def fix_zip_filename(filename):
    try:
        unicode_name = str(bytes(filename, encoding='cp437'), encoding='cp866')
    except UnicodeEncodeError:
        unicode_name = filename
    return unicode_name

def parse_jtv(c, settings):
    print_with_time("Trying parsing as JTV...")
    zf = zipfile.ZipFile(io.BytesIO(c), "r")
    array = {}
    tvguide_sets = {}
    for fileinfo in zf.infolist():
        fn = fix_zip_filename(fileinfo.filename)
        if fn.endswith('.pdt'):
            n = fn[0:-4].replace('_', ' ')
            if not n in array:
                array[n] = {}
            array[n]['titles'] = parse_titles(zf.read(fileinfo))
        if fn.endswith('.ndx'):
            n = fn[0:-4].replace('_', ' ')
            if not n in array:
                array[n] = {}
            array[n]['schedules'] = parse_schedule(zf.read(fileinfo), settings)
    array_out = {}
    for chan in array:
        array_out[chan] = []
        ic = -1
        for title in array[chan]['titles']:
            ic += 1
            dt = array[chan]['schedules'][ic]
            try:
                dt2 = array[chan]['schedules'][ic+1]
                array_out[chan].append({
                    'start': dt,
                    'stop': dt2,
                    'title': title,
                    'desc': ' '
                })
            except: # pylint: bare-except
                pass
    return array_out
