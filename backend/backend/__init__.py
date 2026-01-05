# init.py = 장고 프로젝트의 패키지 초기화 파일
# absolute_import = celery.py와 celery 라이브러리의 충돌 방지
# unicode_literals = 모든 문자열 리터럴을 유니코드로 처리
from __future__ import absolute_import, unicode_literals
# 같은 디렉토리(backend)의 celery 의 app 객체 import
from .celery import app as celery_app
# klub_talk의 task import
from klub_talk.tasks import *
# 이 패키지를 import로 불러올 때, celery_app만 외부로 노출 -> 다른 프로젝트에서 celery_app을 사용할 수 있게 함
__all__ = ('celery_app',)

# init.py = celery 사용 + 설정 + 작업(task)를 정의하는 역할