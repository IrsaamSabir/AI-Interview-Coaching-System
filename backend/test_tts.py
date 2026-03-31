import httpx
r = httpx.post('http://127.0.0.1:8000/api/v1/speech/tts', json={'text': 'whats the update regrading portfolio asad'})
open('test_audio.mp3', 'wb').write(r.content)
print('saved to test_audio.mp3')
