import datetime
import json
import logging
from fastapi import APIRouter, UploadFile, File
from app_en.services.speech_to_text import speech2text, save_speech_file
from app_en.config import config
import aiofiles


router = APIRouter()
@router.post("/speech")
async def upload_file(file: UploadFile = File(...)):
    logging.info("(1)收到语音查询请求，准备存储文件")
    saved_info = await save_speech_file(file)
    file_path = saved_info['file_path']
    logging.info(f"(2)文件完成存储：{file_path}")
    result = speech2text(file_path)
    logging.info("(3)文件完成讯飞接口的转文字")
    logging.info(f"(4)文字转出结果为：{result}")
    await save_text(result)
    return {'text': result}

 # 保存采集到的语音转文字结果
async def save_text(result):
    async with aiofiles.open(config.TEXT_PATH, 'a+') as fw:
        await fw.write(json.dumps({'time': str(datetime.datetime.now()), 'text': result}, ensure_ascii=False)+'\n')