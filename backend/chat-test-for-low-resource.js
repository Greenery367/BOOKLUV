import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// 1. 방 개수를 줄여서 특정 방에 부하 집중 (병목 현상 유도)
// Railway 같은 저사양에서는 많은 방을 관리하는 것보다 한 방에 사람이 몰릴 때 CPU가 먼저 터집니다.
const VALID_SLUGS = ['test-room', 'hot-topic-1', 'hot-topic-2']; 

export const options = {
    stages: [
        { duration: '1m', target: 1000 },  // 10초가 아니라 1분 동안 천천히 1000명까지 올리기
        { duration: '2m', target: 1000 },  // 1000명 유지하며 버티기
        { duration: '30s', target: 0 },
    ],
    // 저사양에서는 지연 시간 기준을 현실적으로 조정 (안 그러면 계속 빨간불 뜹니다)
    thresholds: {
        'checks': ['rate>0.90'],          // 90%만 성공해도 대성공
        'ws_msg_latency': ['p(95)<1000'], // 1초 이내 응답 목표
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
            // [수정] 메시지 전송 주기를 짧게 해서 서버의 CPU를 더 괴롭힙니다.
            socket.setInterval(() => {
                const payload = {
                    type: 'chat',
                    message: `VU ${__VU}: 저사양 테스트 메시지`,
                    ts: Date.now(),
                };
                socket.send(JSON.stringify(payload));
                msgSent.add(1);
            }, Math.floor(Math.random() * 1000) + 500); // 0.5~1.5초 간격 (더 빡세게!)
        });

        socket.on('message', (data) => {
            msgReceived.add(1);
            try {
                const msg = JSON.parse(data);
                if (msg.ts) {
                    msgLatency.add(Date.now() - msg.ts);
                }
            } catch (e) {}
        });

        // 세션 유지 시간을 짧게 하여 잦은 연결/해제(Handshake) 부하를 테스트합니다.
        socket.setTimeout(() => socket.close(), 30000); 
    });

    check(res, { 'WS 연결 성공(101)': (r) => r && r.status === 101 });
    sleep(Math.random() * 3); // 유저들의 접속 타이밍을 분산시켜 실제와 비슷하게 만듭니다.
}