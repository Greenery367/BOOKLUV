import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
# 장고가 관리하는 모델, 앱 설정을 메모리에 올림
django.setup()
# 표준 HTTP 요청(API) 처리를 위한 ASGI 애플리케이션 생성
django_asgi_app = get_asgi_application()

# import error 방지를 위해 설정 후 import
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from klub_chat.consumers import ChatConsumer, MeetingAlertConsumer

# 프로토콜 라우팅 설정
# protocolTypeRouter = 어떤 프로토콜(HTTP/WS)이냐에 따라 경로 분기
application = ProtocolTypeRouter({
    # HTTP -> django_asgi_app
    "http": django_asgi_app,
    # WebSocekt -> 
    "websocket": AuthMiddlewareStack(  
        # AuthMiddlewareStack = 장고 표준 세션 인증을 WS에서도 쓸 수 있게 해줌
        URLRouter([ 
            # 채팅방 연결 처리
            path('ws/chat/<room_name>/', ChatConsumer.as_asgi()),
            # 미팅 알람 처리
            path('ws/meeting-alerts/', MeetingAlertConsumer.as_asgi()),
        ])
    ),
})