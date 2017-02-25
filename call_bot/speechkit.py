import xml.etree.ElementTree as XmlElementTree
import httplib2
import urllib.request
import urllib.parse
import uuid
import alsaaudio
import numpy
import time
import struct
import os
import translit
import config

YANDEX_ASR_HOST = 'asr.yandex.net'
YANDEX_ASR_PATH = '/asr_xml'
CHUNK_SIZE = 1024 ** 2
RATE = 16000
PCM_CHUNK = 1024
THRESHOLD_AFTER_ACTIVATION = 200
THRESHOLD = 200

launch_time = time.time()

def log(s):
    elapsed = time.time() - launch_time
    print(("[%02d:%02d] " % (int(elapsed//60), int(elapsed%60))) + str(s))

def read_chunks(chunk_size, byte_data):
    while True:
        chunk = byte_data[:chunk_size]
        byte_data = byte_data[chunk_size:]

        yield chunk

        if not byte_data:
            break

def enoughVolume(data):
    # преобразовываем массив байтов в Сишную структуру данных
    frames = struct.unpack("<" + str(PCM_CHUNK) + "h", data)  # строка -> список из CHUNK отсчетов, h - это short int

    s = 0
    # суммируем модули отсчетов - они могут быть отрицательными
    for frame in frames:
        s += abs(frame)

    return s // RATE > THRESHOLD


def record():
    log("Жду пока ты что-то скажешь")
    recorder = alsaaudio.PCM(
        type=alsaaudio.PCM_CAPTURE,
        mode=alsaaudio.PCM_NORMAL,
        device='default'
    )
    recorder.setchannels(1)
    recorder.setrate(16000)
    recorder.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    recorder.setperiodsize(1024)

    f = bytes()
    silent_chunks = 0 # сколько чанков юзер молчал
    started_talking = False
    talking_logged = False
    while True:
        # Read data from device
        l, data = recorder.read()

        if (started_talking and not talking_logged): 
            log("Жду пока ты замолчишь")
            talking_logged = True

        if l:
            started_talking = True
            if not enoughVolume(data):
                silent_chunks += 1
            f += data
            time.sleep(.001)

        if silent_chunks > 25:
            log("Конец записи")
            return f

def record_to_text(request_id=uuid.uuid4().hex, topic='notes', lang='ru-RU',
                   key=config.YANDEX_API_KEY):

    log("Считывание блока байтов")
    chunks = read_chunks(CHUNK_SIZE, record())

    log("Установление соединения")
    connection = httplib2.HTTPConnectionWithTimeout(YANDEX_ASR_HOST)

    url = YANDEX_ASR_PATH + '?uuid=%s&key=%s&topic=%s&lang=%s' % (
        request_id,
        key,
        topic,
        lang
    )

    log("Запрос к Yandex API")
    connection.connect()
    connection.putrequest('POST', url)
    connection.putheader('Transfer-Encoding', 'chunked')
    connection.putheader('Content-Type', 'audio/x-pcm;bit=16;rate=16000')
    connection.endheaders()

    log("Отправка записи")
    for chunk in chunks:
        connection.send(('%s\r\n' % hex(len(chunk))[2:]).encode())
        connection.send(chunk)
        connection.send('\r\n'.encode())

    connection.send('0\r\n\r\n'.encode())
    response = connection.getresponse()

    log("Обработка ответа сервера")
    if response.code == 200:
        response_text = response.read()
        xml = XmlElementTree.fromstring(response_text)

        if int(xml.attrib['success']) == 1:
            max_confidence = - float("inf")
            text = ''

            for child in xml:
                if float(child.attrib['confidence']) > max_confidence:
                    text = child.text
                    max_confidence = float(child.attrib['confidence'])

            if max_confidence != - float("inf"):
                return text
            else:
                raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
        else:
            raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
    else:
        raise SpeechException('Unknown error.\nCode: %s\n\n%s' % (response.code, response.read()))

def record_to_text_looped(error_message):
    while True:
        try:
            return record_to_text()
        except Exception as e:
            tts(error_message)

def play_wav(path):
    os.system("play " + path)

def tts(text):
    '''
    https://tts.voicetech.yandex.net/generate?
          text=<текст для озвучивания>
        & format=<формат аудио файла>
        & lang=<язык>
        & speaker=<голос>
        & key=<API‑ключ>

        & [emotion=<эмоциональная окраска голоса>]
        & [speed=<скорость речи>]
    '''
    log("Преобразование текста в речь")
    filename = translit.translit(text) + '.wav'
    if not os.path.exists('tts/' + filename):
        url = 'https://tts.voicetech.yandex.net/generate?text={text}&format=wav&lang=ru-RU&speaker=jane&key={key}'.format(
            text=urllib.parse.quote(text), 
            key=config.YANDEX_API_KEY)
        urllib.request.urlretrieve(url, 'tts/' + filename)
    else: log("Ура! Эта реплика есть в кэше")
    log("Голос говорит: " + text)
    log("="*30)
    log("Воспроизведение файла: ")
    play_wav('tts/' + filename)
    log("="*30)

class SpeechException(Exception):
    pass