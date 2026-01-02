import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const VALID_SLUGS = ['test-room', 'hot-topic-1']; 

export const options = {
    stages: [
        { duration: '1m', target: 1000 },  
        { duration: '2m', target: 1000 },  
        { duration: '30s', target: 0 },    
    ],
    thresholds: {
        'checks': ['rate>0.95'],           
        'ws_msg_latency': ['p(95)<1000'],  
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
                const payload = {
                    m: `V${__VU}`,
                    s: Date.now(),
                };
                const jsonStr = JSON.stringify(payload);
                const buf = new ArrayBuffer(jsonStr.length);
                const bufView = new Uint8Array(buf);
                for (let i = 0; i < jsonStr.length; i++) {
                    bufView[i] = jsonStr.charCodeAt(i);
                }

                socket.sendBinary(buf); 
                msgSent.add(1);
            }, 5000); 
        });

        socket.on('message', (data) => {
            msgReceived.add(1);
        });

        socket.on('error', (e) => {
            console.error("WS Error: ", e.error());
        });

        socket.setTimeout(() => socket.close(), 30000); 
    });

    check(res, { 'WS 연결 성공(101)': (r) => r && r.status === 101 });
    sleep(Math.random() * 5); 
}