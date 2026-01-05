import ws from 'k6/ws';
import { check, sleep } from 'k6';

export const options = {
    scenarios: {
        default: {
            executor: 'per-vu-iterations', // [변경] 루프를 돌지 않고, 딱 1번씩만 성공시키기
            vus: 1000,
            iterations: 1, // 각 유저는 딱 한 번의 성공을 위해 도전합니다.
            maxDuration: '10m',
        },
    },
};

export default function () {
    // 유저 번호(__VU)에 따라 입장 시간을 0초부터 300초(5분)까지 골고루 분산합니다.
    // 0.1 CPU가 한 명씩 차례대로 받을 수 있게 줄을 길게 세우는 전략입니다.
    const delay = (__VU - 1) * 0.3; 
    sleep(delay);

    const URL = `ws://localhost:8001/ws/chat/test-room/`;
    const params = { handshakeTimeout: 120000 };

    const res = ws.connect(URL, params, function (socket) {
        socket.on('open', () => {
            // 연결 성공 시 5초간 유지
            socket.setTimeout(() => socket.close(), 5000);
        });
    });

    check(res, { 'WS 연결 성공(101)': (r) => r && r.status === 101 });
}