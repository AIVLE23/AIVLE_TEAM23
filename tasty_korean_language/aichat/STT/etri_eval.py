import json
import urllib3
import base64
import librosa
import numpy as np
from typing import Tuple

def load_and_convert_audio(audio_path: str) -> np.ndarray:
    audio, sr = librosa.load(audio_path, sr=16000)
    return (audio * 32767).astype(np.int16)

def create_etri_request(script: str, pcm_data: np.ndarray, api_key: str) -> Tuple[str, dict]:
    base64_audio = base64.b64encode(pcm_data).decode('utf-8')
    
    return (
        "http://aiopen.etri.re.kr:8000/WiseASR/PronunciationKor",
        {
            "headers": {
                "Content-Type": "application/json; charset=UTF-8",
                "Authorization": api_key
            },
            "body": json.dumps({
                "argument": {
                    "language_code": "korean",
                    "script": script,
                    "audio": base64_audio
                }
            })
        }
    )

def etri_eval(origin_text: str, audio_path: str, api_key: str) -> float:

    try:
        # 오디오 파일 전처리
        pcm_data = load_and_convert_audio(audio_path)
        
        # API 요청 생성
        endpoint, request_data = create_etri_request(origin_text, pcm_data, api_key)
        
        # API 호출
        http = urllib3.PoolManager()
        response = http.request("POST", endpoint, **request_data)
        
        # 결과 파싱
        result = json.loads(response.data)['return_object']['score']
        return round(float(result), 1)
        
    except KeyError as e:
        raise ValueError("Invalid API response structure") from e
    except json.JSONDecodeError as e:
        raise ValueError("Failed to parse JSON response") from e
    except Exception as e:
        raise RuntimeError(f"API call failed: {str(e)}") from e