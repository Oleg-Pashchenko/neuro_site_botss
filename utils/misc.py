import os
import random

import whisper
import requests


async def wisper_detect(link: str):
    r = requests.get(link, allow_redirects=True)
    filename = f'{random.randint(10000000, 100000000)}.m4a'
    open(filename, 'wb').write(r.content)
    model = whisper.load_model("base")

    # load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio(filename)
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    _, probs = model.detect_language(mel)
    options = whisper.DecodingOptions(fp16=False)
    result = whisper.decode(model, mel, options)
    return result.text



def download_file(db_name):
    if not os.path.exists(db_name):
        print('Donwloading file')
        import gdown
        file_id = db_name.split("id=")[1]
        try:
            download_url = f"https://drive.google.com/uc?id={file_id}"
            print(download_url)
            output_path = f"files/{file_id}.xlsx"
            gdown.download(download_url, output_path, quiet=True)
        except:
            pass