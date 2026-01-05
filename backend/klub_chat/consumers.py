import json
import os
import time
import random  # 🔥 누락되었던 모듈 추가
import redis.asyncio as redis
import msgpack
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
import logging
from .models import Room
from klub_talk.models import Meeting, Participate


# =====================
# Redis (전역 커넥션 풀)
# =====================
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
logger = logging.getLogger(__name__)

redis_pool = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=500,   # 🔥 부하 테스트 시 커넥션 수 확보
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
        
    async def disconnect(self, close_code):
        # 그룹 퇴장
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            # MessagePack 진공 포장 뜯기
            if bytes_data:
                data = msgpack.unpackb(bytes_data)
            elif text_data:
                data = json.loads(text_data)
            else:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "m": data.get("m"), 
                    "u": self.user_nickname, 
                    "i": self.user_id,
                    "s": data.get("s"), 
                }
            )
        except Exception as e:
            logger.error(f"❌ 데이터 해독 실패: {e}")

    async def chat_message(self, event):
        payload = {
            "t": "c",
            "m": event["m"],
            "u": event["u"],
            "i": event["i"],
            "s": event["s"],
        }
        # bytes_data로 전송 (완벽함)
        await self.send(bytes_data=msgpack.packb(payload))

    # [보너스] 참가자 상태 전송도 MessagePack으로 통일하면 더 좋음
    async def participants_status(self, event):
        payload = {
            "type": "participants",
            "participants": event["participants"],
        }
        # 여기도 bytes_data로 보내야 프론트엔드가 안 터져요!
        await self.send(bytes_data=msgpack.packb(payload))

    # [수정] 아래 로직들은 별도의 헬퍼 함수나 기존 함수 안에 있어야 합니다.
    async def get_participants_status(self):
        meeting = await self.get_meeting()
        if not meeting:
            return []

        users = await self.get_confirmed_users(meeting)
        # self.redis가 아닌 위에서 정의한 redis_pool을 사용해야 할 수도 있습니다.
        key = f"chat_room_users_{self.room.slug}"
        # decode_responses=True인 풀을 사용하므로 map(int) 사용 시 주의!
        online_ids = set(map(int, await redis_pool.smembers(key)))

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

    # [수정] 알람도 MessagePack으로 진공 포장
    async def send_meeting_alert(self, event):
        payload = {
            "title": event["title"],
            "started_at": event["started_at"],
            "meeting_id": event["meeting_id"],
            "join_url": event.get("join_url", "#"),
        }
        await self.send(bytes_data=msgpack.packb(payload))