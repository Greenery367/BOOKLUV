from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger 문서 설정
schema_view = get_schema_view(
    openapi.Info(
        # 문서 제목
        title="BOOKLUV API",
        # 버전
        default_version="v1",
        # 설명
        description="BOOKLUV 백엔드 API 문서",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# 임시 메인 페이지
# def home(request):
#     return HttpResponse("로그인 성공!") 

urlpatterns = [
    # 관리자 페이지
    path('admin/', admin.site.urls),
    # 유저  - 로그인
    path("api/v1/auth/", include('klub_user.urls')),
    # 유저 - 자유게시판, 댓글 
    path('api/v1/board/', include('klub_board.api_urls', namespace='board')),
    # 유저 - 책, 모임 정보
    path("api/v1/books/", include("klub_talk.api_urls")),
    # 유저 - 책, 모임 정보 (백엔드 확인 용)
    path("api/v1/book/", include("klub_talk.urls")),
    # 유저 - 실시간 채팅 및 알람
    path("api/v1/chat/", include("klub_chat.urls")),
    # 유저 - AI API 기반 추천 기능
    path("api/v1/recommendations/", include("klub_recommend.urls")),

    # Swagger 
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
]
