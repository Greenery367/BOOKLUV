import os
from celery import Celery

# Celery가 장고의 설정을 읽을 수 있게 경로 설정 -> backend 폴더 내부의 settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# backend라는 이름의 Celery 객체 생성
app = Celery('backend')
# settings.py 내부의 CELERY로 시작하는 설정들을 찾아 Celery 설정으로 사용
app.config_from_object('django.conf:settings', namespace='CELERY')
# klub_talk 내부의 task를 자동으로 찾아 작업을 등록함
app.autodiscover_tasks(['klub_talk'])

# Celery beat의 스케줄러 설정 (10초에 1번씩)
app.conf.beat_schedule = {
    # 미팅별 룸(채팅방) 생성
    'create-rooms-every-minute': {
        'task': 'klub_talk.tasks.check_and_create_rooms',
        'schedule': 10.0,
    },
    # 오늘 있을 알람 생성
    'send_today_meeting_alarms_for_today': {
        'task': 'klub_talk.tasks.send_today_meeting_alarms_for_today',
        'schedule': 10.0,
    },
    # 미팅 시스템 메세지 전송
    "send_meeting_system_messages": {
        "task": "klub_talk.tasks.send_meeting_system_messages",
        'schedule': 10.0,
    },
}

# 한국 시간 기준으로 스케줄링
app.conf.timezone = 'Asia/Seoul'

# 만약 autodiscover가 task를 찾지 못할 경우를 대비 -> 강제 import
from klub_talk import tasks
