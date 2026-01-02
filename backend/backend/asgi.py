import os
import django
from django.core.asgi import get_asgi_application

# 1. 환경 변수 설정 (반드시 가장 먼저!)
# 'your_project.settings'를 실제 프로젝트 명인 'backend.settings'로 수정함
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# 2. Django 초기화 (앱 로딩 완료)
django.setup()

# 3. HTTP ASGI 애플리케이션 미리 생성
django_asgi_app = get_asgi_application()

# 4. 앱 로딩 후 컨슈머 및 라우팅 임포트 (중요!)
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from klub_chat.consumers import ChatConsumer, MeetingAlertConsumer

# 5. 프로토콜 라우팅 설정
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(  # 인증이 필요하면 다시 넣으셔도 됩니다.
        URLRouter([  # 여기서 리스트([])로 경로를 바로 감쌉니다.
            path('ws/chat/<room_name>/', ChatConsumer.as_asgi()),
            path('ws/meeting-alerts/', MeetingAlertConsumer.as_asgi()),
        ])
    ),
})