import json
import redis
import os
from datetime import timedelta
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

from django.core.exceptions import ObjectDoesNotExist

from .models import Room
from klub_talk.models import Meeting, Participate

# =====================
# Redis 설정 (Railway URL 반영)
# =====================
REDIS_URL = os.getenv('REDIS_URL')

# =====================
# 채팅방 목록 (자동 생성 및 필터링)
# =====================

def room_list(request):
    # [수정] 모든 방이 다 나오도록 필터링을 잠시 주석 처리하거나 범위를 넓힙니다.
    rooms = Room.objects.all().select_related("meeting") 

    return render(request, "chat/room_list.html", {
        "rooms": rooms,
        "user": request.user,
    })
# =====================
# 채팅방 상세 (Redis 인증 에러 해결)
# =====================

def room_detail(request, room_name):
    room = get_object_or_404(Room, slug=room_name)
    meeting = getattr(room, "meeting", None)
    
    # [테스트용] 로그인하지 않은 유저에게 가상 ID와 닉네임 부여
    user = request.user
    if not user.is_authenticated:
        test_user_id = request.GET.get('vu', '999') # k6에서 넘겨줄 VU 번호
        nickname = f"Tester_{test_user_id}"
    else:
        nickname = getattr(user, 'nickname', '익명')
        
    participants_list = [] 
    
    # [수정] 리스트가 비어있지 않고 meeting 정보가 있을 때만 정렬 실행
    if participants_list and meeting and meeting.leader_id:
        participants_list.sort(key=lambda x: x['id'] != meeting.leader_id.id)

    now = timezone.now()
    can_chat = True # 무조건 채팅 가능하게 설정
    
    # 리더를 맨 앞으로 정렬
    participants_list.sort(key=lambda x: x['id'] != meeting.leader_id.id)

    # Redis 메시지 로드
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        messages_raw = r.lrange(f"chat_{room.slug}", 0, -1)
    except Exception as e:
        print(f"Redis 연결 실패: {e}")
        messages_raw = []

    messages = []
    for m in messages_raw:
        try:
            msg = json.loads(m)
            if "timestamp" in msg:
                dt = timezone.datetime.fromisoformat(msg["timestamp"])
                # [수정] naive 체크 후 aware로 변환하여 안전하게 출력
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                msg["timestamp"] = timezone.localtime(dt).strftime("%Y-%m-%d %H:%M:%S")
            messages.append(msg)
        except Exception:
            continue

    return render(request, "chat/room_detail.html", {
        "room": room,
        "nickname": nickname, # 가상 닉네임 전달
        "messages": messages,
        "can_chat": can_chat,
        "participants": participants_list,
        "total_members": 100, # 더미 수치
    })

# =====================
# 오늘의 미팅 알람 (수정 완료)
# =====================

def today_meetings(request):
    user = request.user
    # [수정] 알람도 일단 모든 미팅이 다 나오게 변경
    meetings_today = Meeting.objects.all().select_related("room", "leader_id")

    data = []
    for m in meetings_today:
        # [수정] 테스트를 위해 리더/참여자 체크도 잠시 통과시킴
        # is_leader = m.leader_id == user
        # is_participant = m.participations.filter(user_id=user, result=True).exists()
        # if not (is_leader or is_participant): continue

        try:
            room = m.room
        except ObjectDoesNotExist:
            room = None

        if room:
            data.append({
                "meeting_id": m.id,
                "title": m.title,
                "started_at": timezone.localtime(m.started_at).strftime("%H:%M"),
                "room_slug": room.slug,
                "join_url": f"/api/v1/chat/rooms/{room.slug}/",
            })

    return JsonResponse({"meetings": data})