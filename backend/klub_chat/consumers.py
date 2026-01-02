import json
import os
import time
import random  # 🔥 누락되었던 모듈 추가
import redis.asyncio as redis

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings

from .models import Room
from klub_talk.models import Meeting, Participate


# =====================
# Redis (전역 커넥션 풀)
# =====================
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_pool = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=20,   # 🔥 부하 테스트 시 커넥션 수 확보
)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        
        # 유저 인증 및 익명 처리
        user = self.scope["user"]
        if not user.is_authenticated:
            self.user_id = 9999 + random.randint(1, 1000)
            self.user_nickname = f"Tester_{self.user_id}"
        else:
            self.user_id = user.id
            self.user_nickname = getattr(user, 'nickname', '익명')

        # 🛑 에러 방지: DB 조회 실패해도 연결은 유지
        try:
            self.room = await self.get_room()
        except Exception:
            class Mock: pass
            self.room = Mock()
            self.room.slug = self.room_name

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept() # 이 메서드가 호출되어야 연결이 유지됨
    async def disconnect(self, close_code):
        # 그룹 퇴장
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            # 그룹 전체에 메시지 전송
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "m": data.get("m"), # message -> m
                    "u": self.user_nickname, 
                    "i": self.user_id,
                    "s": data.get("s"), # ts -> s
                }
            )
        except Exception as e:
            print(f"error: {e}")

    async def chat_message(self, event):
        # 브라우저로 메시지 전송
        await self.send(text_data=json.dumps({
            "t": "c",
            "m": event["m"],
            "u": event["u"],
            "i": event["i"],
            "s": event.get("s"),
        }))

    async def system_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "system",
            "message": event["message"],
            "ts": time.time(),
        }))

    # =====================
    # 참가자 상태 관련 (필요 시 주석 해제)
    # =====================
    async def add_online_user(self):
        key = f"chat_room_users_{self.room.slug}"
        # self.user.id 대신 정의된 self.user_id 사용
        await self.redis.sadd(key, self.user_id)

    async def remove_online_user(self):
        key = f"chat_room_users_{self.room.slug}"
        await self.redis.srem(key, self.user_id)

    async def broadcast_participants_status(self):
        participants = await self.get_participants_status()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "participants_status",
                "participants": participants,
            }
        )

    async def participants_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "participants",
            "participants": event["participants"],
        }))

    async def get_participants_status(self):
        meeting = await self.get_meeting()
        if not meeting:
            return []

        users = await self.get_confirmed_users(meeting)
        key = f"chat_room_users_{self.room.slug}"
        online_ids = set(map(int, await self.redis.smembers(key)))

        return [
            {
                "id": user.id,
                "nickname": getattr(user, 'nickname', '익명'),
                "online": user.id in online_ids,
            }
            for user in users
        ]

    # =====================
    # DB helpers (Async 안전)
    # =====================
    @database_sync_to_async
    def get_room(self):
        return Room.objects.select_related("meeting").get(slug=self.room_name)

    @database_sync_to_async
    def get_meeting(self):
        return getattr(self.room, "meeting", None)

    @database_sync_to_async
    def get_confirmed_users(self, meeting):
        users = {}
        if meeting.leader_id:
            users[meeting.leader_id.id] = meeting.leader_id

        participants = Participate.objects.filter(
            meeting=meeting,
            result=True
        ).select_related("user_id")

        for p in participants:
            users[p.user_id.id] = p.user_id
        return list(users.values())


# =========================
# 🔔 미팅 알람 Consumer
# =========================
class MeetingAlertConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "meeting_alerts"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_meeting_alert(self, event):
        await self.send(text_data=json.dumps({
            "title": event["title"],
            "started_at": event["started_at"],
            "meeting_id": event["meeting_id"],
            "join_url": event.get("join_url", "#"),
        }))