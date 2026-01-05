import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// 100개의 채팅 방 입장을 위한 room slug 준비
const VALID_SLUGS = ['test-room'];
for (let i = 1; i <= 99; i++) {
    VALID_SLUGS.push(`room-slug-${i}`);
}

// 부하 시나리오 : 1000명의 유저가 100개의 채팅방에 접속
export const options = {
    stages: [
        // 10초 : 500명 접속
        { duration: '10s', target: 500 },  
        // 그 후 20초 동안 1000명까지 추가 접속
        { duration: '20s', target: 1000 }, 
        // 1000명이 유지된 상태로 1분간 동시 접속 유지
        { duration: '1m', target: 1000 },  
        // 테스트 종료
        { duration: '10s', target: 0 }, 
    ],
    // 테스트 통과 기준
    thresholds: {
        // 연결 성공률 99% 이상
        checks: ['rate>0.99'],          
        // 95%는 0.3초 이내에 전달되어야 함
        ws_msg_latency: ['p(95)<300'],  
    },
};

// 서버로부터 받은 총 메세지 수
const msgReceived = new Counter('ws_msg_received');
// 서버로 보낸 총 메세지 수
const msgSent = new Counter('ws_msg_sent');
// 메세지 전달 시간 (지연 시간)
const msgLatency = new Trend('ws_msg_latency');


export default function () {
    // 100개의 방 중 하나에 랜덤 접속 -> url+room_slug
    const slug = VALID_SLUGS[Math.floor(Math.random() * VALID_SLUGS.length)];
    
    // WS 전용 Daphne 서버로 접속
    const URL = `ws://localhost:8001/ws/chat/${slug}/`;

    // WS 연결 시도
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