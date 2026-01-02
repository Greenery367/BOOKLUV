import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// 특정 방에 부하를 집중시켜 실제 대규모 채팅 상황 재현
const VALID_SLUGS = ['test-room', 'hot-topic-1']; 

export const options = {
    stages: [
        { duration: '1m', target: 1000 },  // 1분 동안 천천히 1000명까지 증가 (Ramp-up)
        { duration: '2m', target: 1000 },  // 1000명 유지하며 버티기 (Peak)
        { duration: '30s', target: 0 },    // 종료 (Ramp-down)
    ],
    thresholds: {
        'checks': ['rate>0.95'],           // 성공률 95% 이상 목표
        'ws_msg_latency': ['p(95)<1000'],  // 페이로드 다이어트 후 1초 이내 응답 목표
    },
};

const msgReceived = new Counter('ws_msg_received');
const msgSent = new Counter('ws_msg_sent');
const msgLatency = new Trend('ws_msg_latency');

export default function () {
    const slug = VALID_SLUGS[Math.floor(Math.random() * VALID_SLUGS.length)];
    const URL = `ws://localhost:8001/ws/chat/${slug}/`;

    const res = ws.connect(URL, null, function (socket) {
        
        socket.on('open', () => {
            socket.setInterval(() => {
                // [페이로드 다이어트 적용]
                // 서버 consumers.py에서 처리할 수 있도록 짧은 키값 사용
                const payload = {
                    m: `V${__VU}`,    // message -> m (최소화)
                    s: Date.now(),    // ts -> s
                };
                socket.send(JSON.stringify(payload));
                msgSent.add(1);
            }, 5000); // 전송 주기를 5초로 현실화 (1000명이 0.5초마다 쏘면 0.1 CPU는 무조건 죽습니다)
        });

        socket.on('message', (data) => {
            msgReceived.add(1);
            try {
                const msg = JSON.parse(data);
                // [지연 시간 측정 수정] 
                // 서버가 보내주는 짧은 키값 's'를 사용하여 측정
                if (msg.s) {
                    msgLatency.add(Date.now() - msg.s);
                }
            } catch (e) {}
        });

        // 세션 유지 (Railway 환경의 타임아웃을 고려하여 30초 유지)
        socket.setTimeout(() => socket.close(), 30000); 
    });

    check(res, { 'WS 연결 성공(101)': (r) => r && r.status === 101 });
    sleep(Math.random() * 5); // 접속 타이밍 분산
}