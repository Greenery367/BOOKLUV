// 0.1 CPU + 512MB 메모리 환경의 저사양 환경에서 k6 부하테스트 실행
// 목표: 1,000명의 동시 접속자가 100개의 채팅방에 입장하는 상황에서 연결률 100% 달성

// k6 WebSocket import
import ws from 'k6/ws';
// 테스트 검증 / 실행 중지 기능 import
import { check, sleep } from 'k6';

// 100개의 채팅방에 대한 room slug 준비
const VALID_SLUGS = [];
for (let i = 1; i <= 99; i++) {
    VALID_SLUGS.push(`room-slug-${i}`);
}
VALID_SLUGS.push('test-room');

export const options = {
    scenarios: {
        default: {
            // 반복 횟수를 기준으로 테스트 실행
            executor: 'per-vu-iterations', 
            // 동시에 가상유저(VU) 1,000명 실행
            vus: 1000,
            // 각 유저는 딱 한 번만 테스트 시나리오 실행 후 종료
            iterations: 1, 
            // 아무리 길어져도 10분 후에는 강제 종룐
            maxDuration: '10m',
        },
    },
};

export default function () {
    // 유저마다 0.3초씩 지연시간을 두어 연결 시킴
    // 1번 유저 - > 0초 / 2번 유저 -> 0.3초 / 3번 유저 -> 0.6초...
    const delay = (__VU - 1) * 0.3; 
    sleep(delay); // 계산된 delay 시간만큼 대기 후 실행

    // 100개의 방 중 핸덤한 방 하나에 접속
    const slug = VALID_SLUGS[Math.floor(Math.random() * VALID_SLUGS.length)];

    // 테스트를 진행할 채팅방 url
    const URL = `ws://localhost:8001/ws/chat/${slug}/`;
    // handshake timeout = 2분으로 설정
    const params = { handshakeTimeout: 120000 };

    // 위에서 설정한 URL / handshake 설정으로 연결 시도
    const res = ws.connect(URL, params, function (socket) {
        // 연결 성공 시
        socket.on('open', () => {
            // 5초 유지
            // 즉, 한 명당 5초 동안 서버에 머물며 부하 유지
            socket.setTimeout(() => socket.close(), 5000);
        });
        socket.on('error', (e) => {
            console.error(`[VU ${__VU} - 방: ${slug}] 에러 발생: ${e.error()}`);
        });
    });
    sleep(10);
    // 연결 결과(res)가 정상인지 확인
    // HTTP = 101일 시 성공
    check(res, { 'WS 연결 성공(101)': (r) => r && r.status === 101 });
}