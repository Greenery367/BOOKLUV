import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// 1. 100개의 채팅방 슬러그 준비 (DB 데이터 반영)
const VALID_SLUGS = ['test-room'];
for (let i = 1; i <= 99; i++) {
    VALID_SLUGS.push(`room-slug-${i}`);
}

// 2. 부하 시나리오: 총 1,000명의 유저가 100개 방에 동시 접속
export const options = {
    stages: [
        { duration: '10s', target: 500 },  // 10초 동안 500명까지 증가
        { duration: '20s', target: 1000 }, // 30초 시점에 1000명 도달
        { duration: '1m', target: 1000 },  // 1분간 토론 피크 타임 유지
        { duration: '10s', target: 0 },    // 종료
    ],
    thresholds: {
        checks: ['rate>0.99'],          // 연결 실패율 1% 미만 유지
        ws_msg_latency: ['p(95)<300'],  // 로컬이므로 지연 시간 0.3초 이내 권장
    },
};

const msgReceived = new Counter('ws_msg_received');
const msgSent = new Counter('ws_msg_sent');
const msgLatency = new Trend('ws_msg_latency');

export default function () {
    // 100개의 방 중 하나에 랜덤 접속
    const slug = VALID_SLUGS[Math.floor(Math.random() * VALID_SLUGS.length)];
    
    // 로컬호스트 Daphne 웹소켓 포트(8001)로 설정
    const URL = `ws://localhost:8001/ws/chat/${slug}/`;

    const res = ws.connect(URL, null, function (socket) {
        
        socket.on('open', () => {
            // 실시간 토론 모사: 2~4초 사이의 짧은 간격으로 메시지 전송
            socket.setInterval(() => {
                const payload = {
                    type: 'chat',
                    message: `로컬 테스트 메시지 - VU ${__VU}: 토론 중입니다!`,
                    ts: Date.now(),
                };
                socket.send(JSON.stringify(payload));
                msgSent.add(1);
            }, Math.floor(Math.random() * 2000) + 2000); 
        });

        socket.on('message', (data) => {
            msgReceived.add(1);
            try {
                const msg = JSON.parse(data);
                if (msg.type === 'chat' && msg.ts) {
                    const latency = Date.now() - msg.ts;
                    msgLatency.add(latency);
                }
            } catch (e) {
                // 시스템 메시지 등 비정형 데이터 무시
            }
        });

        socket.on('error', (e) => {
            // 연결 실패 시 원인 출력 (포트 문제 등)
            if (e.error()) console.error(`[방: ${slug}] 연결 에러: ${e.error()}`);
        });

        // 세션 유지 (1분 30초)
        socket.setTimeout(() => socket.close(), 90000);
    });

    // HTTP 101 상태 코드가 오는지 확인
    check(res, { '로컬 WS 연결 성공(101)': (r) => r && r.status === 101 });
    
    sleep(1);
}