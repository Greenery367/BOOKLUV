
import os
from django.core.wsgi import get_wsgi_application

# 장고 프로젝트 시작 시 settings.py 설정 파일 참조
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
# WSGI 애플리케이션 객체 생성
application = get_wsgi_application()

# WSGI와 ASGI의 차이
# WSGI : 동기식 HTTP 처리 / 하나의 요청이 끝나야 다음 요청 처리 / Gunicorn
# ASGI : 비동기식 WS 처리 / 여러 연결을 동시에 유지 가능 / Daphne