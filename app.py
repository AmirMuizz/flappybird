import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="F1 2026 Sepang GP", page_icon="🏎️", layout="centered")

st.title("🏎️ F1 2026 Sepang GP (5 Laps)")
st.caption("🏁 **P1:** Arrow Keys + `Shift` (ERS) | **P2:** WASD + `SPACE` (ERS)")

f1_2026_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #121212;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            user-select: none;
            color: white;
        }
        #gameCanvas {
            border: 3px solid #e10600;
            border-radius: 10px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.7);
            background: #1e1e1e;
        }
    </style>
</head>
<body>

<canvas id="gameCanvas" width="680" height="530"></canvas>

<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

let gameState = "SELECT"; 
let winner = "";

const TEAMS = [
    { name: "Oracle Red Bull", color: "#0600ef", accent: "#fcd116", sponsor: "ORACLE" },
    { name: "Scuderia Ferrari", color: "#e8002d", accent: "#ffffff", sponsor: "SHELL" },
    { name: "Mercedes-AMG", color: "#00a29c", accent: "#000000", sponsor: "PETRONAS" },
    { name: "McLaren F1", color: "#ff8000", accent: "#0090ff", sponsor: "ANDROID" },
    { name: "Aston Martin", color: "#229971", accent: "#cedc00", sponsor: "ARAMCO" },
    { name: "Alpine F1", color: "#0093cc", accent: "#ff69b4", sponsor: "BWT" }
];

const SPEED_MODES = [
    { label: "NORMAL", topSpeed: 3.8, accel: 0.09, ersSpeed: 5.2 },
    { label: "FAST ⚡", topSpeed: 4.8, accel: 0.13, ersSpeed: 6.5 },
    { label: "TURBO 🔥", topSpeed: 5.8, accel: 0.17, ersSpeed: 8.0 }
];
let selectedSpeedIdx = 1;

let p1TeamIdx = 0;
let p2TeamIdx = 1;

const trackCenter = [
    {x: 130, y: 450}, // Main Straight
    {x: 540, y: 450}, 
    {x: 600, y: 400}, // T1
    {x: 550, y: 310}, // T2 Hairpin
    {x: 400, y: 310}, // Turn 3
    {x: 280, y: 220}, // T5-6
    {x: 420, y: 140}, // Turn 7-8
    {x: 540, y: 80},  // Back Straight
    {x: 130, y: 80},  
    {x: 80,  y: 200}, // T15 Hairpin
    {x: 80,  y: 370}  
];

class Car {
    constructor(x, y, angle, controls, isP1) {
        this.startX = x;
        this.startY = y;
        this.startAngle = angle;
        
        this.x = x;
        this.y = y;
        this.angle = angle;
        this.speed = 0;
        
        this.controls = controls;
        this.isP1 = isP1;
        this.team = TEAMS[0];
        
        this.ersBattery = 100;
        this.ersBoosting = false;
        
        // Lap & Time System
        this.lap = 1;
        this.maxLaps = 5; // 5 Laps Match
        this.checkpoint = 0;
        
        this.currentLapTime = 0;
        this.bestLapTime = null;
        this.lastLapTime = null;
        this.lapStartTime = 0;
    }

    setTeam(team) {
        this.team = team;
    }

    draw() {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.angle);

        // Rear Wing
        ctx.fillStyle = "#111";
        ctx.fillRect(-16, -7, 4, 14);
        ctx.fillStyle = this.team.accent;
        ctx.fillRect(-16, -8, 2, 16);

        // Wheels
        ctx.fillStyle = "#000";
        ctx.fillRect(-10, -9, 7, 3.5);
        ctx.fillRect(-10, 5.5, 7, 3.5);
        ctx.fillRect(5, -9, 6.5, 3.5);
        ctx.fillRect(5, 5.5, 6.5, 3.5);

        // Body
        ctx.fillStyle = this.team.color;
        ctx.beginPath();
        ctx.moveTo(16, 0);
        ctx.lineTo(6, -4);
        ctx.lineTo(-6, -6);
        ctx.lineTo(-14, -5);
        ctx.lineTo(-14, 5);
        ctx.lineTo(-6, 6);
        ctx.lineTo(6, 4);
        ctx.closePath();
        ctx.fill();

        // Front Wing
        ctx.fillStyle = this.team.accent;
        ctx.fillRect(12, -8, 4, 16);

        // Cockpit & Helmet
        ctx.fillStyle = "#111";
        ctx.fillRect(-2, -3, 6, 6);
        ctx.fillStyle = "#888";
        ctx.beginPath();
        ctx.arc(0, 0, 2, 0, Math.PI * 2);
        ctx.fill();

        // Sponsor Text
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 5px Arial";
        ctx.textAlign = "center";
        ctx.fillText(this.team.sponsor, -4, 1.5);

        if (this.ersBoosting) {
            ctx.fillStyle = "#00f0ff";
            ctx.beginPath();
            ctx.arc(-18, 0, 4 + Math.random()*4, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.restore();
    }

    update(keys, currentTime) {
        if (gameState !== "PLAYING") return;

        let spdMode = SPEED_MODES[selectedSpeedIdx];

        // Track Check
        let isOnTrack = false;
        for (let i = 0; i < trackCenter.length - 1; i++) {
            let p1 = trackCenter[i];
            let p2 = trackCenter[i+1];
            if (distToSegment({x: this.x, y: this.y}, p1, p2) < 28) {
                isOnTrack = true;
                break;
            }
        }

        let maxAllowedSpeed = isOnTrack ? spdMode.topSpeed : 1.1;
        let accelRate = spdMode.accel;
        let brakeRate = 0.22; // Stronger Brakes
        let friction = 0.035;

        // --- Sharp Cornering Physics ---
        // Stereng dinaikkan ke 0.078 rad/frame (lebih tajam untuk selekor hairpin Sepang)
        let turnRatio = Math.min(1.4, Math.max(0.4, Math.abs(this.speed) / spdMode.topSpeed));
        let turnSpeed = 0.078 * turnRatio; 

        if (keys[this.controls.left]) this.angle -= turnSpeed;
        if (keys[this.controls.right]) this.angle += turnSpeed;

        // ERS Boost
        if (keys[this.controls.ers] && this.ersBattery > 0 && keys[this.controls.up] && isOnTrack) {
            this.ersBoosting = true;
            maxAllowedSpeed = spdMode.ersSpeed;
            accelRate = spdMode.accel * 1.6;
            this.ersBattery -= 0.6;
        } else {
            this.ersBoosting = false;
            if (this.ersBattery < 100 && this.speed < 2.0) {
                this.ersBattery += 0.28;
            }
        }

        // Throttle & Brake
        if (keys[this.controls.up]) {
            if (this.speed < maxAllowedSpeed) this.speed += accelRate;
            else this.speed -= friction;
        } else if (keys[this.controls.down]) {
            if (this.speed > -1.2) this.speed -= brakeRate;
        } else {
            if (this.speed > 0) this.speed -= friction;
            if (this.speed < 0) this.speed += friction;
            if (Math.abs(this.speed) < 0.04) this.speed = 0;
        }

        this.x += Math.cos(this.angle) * this.speed;
        this.y += Math.sin(this.angle) * this.speed;

        // Live Lap Timer
        if (this.lapStartTime > 0) {
            this.currentLapTime = (currentTime - this.lapStartTime) / 1000;
        }

        // Checkpoint & Lap Crossing
        let targetCheck = trackCenter[this.checkpoint];
        let dist = Math.hypot(this.x - targetCheck.x, this.y - targetCheck.y);
        if (dist < 55) {
            this.checkpoint = (this.checkpoint + 1) % trackCenter.length;
            if (this.checkpoint === 1) { // Finish Line Crossed
                if (this.lapStartTime > 0) {
                    let completedLapTime = (currentTime - this.lapStartTime) / 1000;
                    this.lastLapTime = completedLapTime;
                    if (!this.bestLapTime || completedLapTime < this.bestLapTime) {
                        this.bestLapTime = completedLapTime;
                    }
                }
                this.lapStartTime = currentTime;
                
                this.lap++;
                if (this.lap > this.maxLaps) {
                    gameState = "GAMEOVER";
                    winner = `${this.isP1 ? 'P1' : 'P2'} (${this.team.name})`;
                }
            }
        }
    }

    reset() {
        this.x = this.startX;
        this.y = this.startY;
        this.angle = this.startAngle;
        this.speed = 0;
        this.ersBattery = 100;
        this.lap = 1;
        this.checkpoint = 0;
        this.currentLapTime = 0;
        this.bestLapTime = null;
        this.lastLapTime = null;
        this.lapStartTime = performance.now();
    }
}

function formatTime(seconds) {
    if (!seconds) return "--:--.--";
    let mins = Math.floor(seconds / 60);
    let secs = (seconds % 60).toFixed(2);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

function distToSegment(p, v, w) {
    let l2 = (v.x - w.x)**2 + (v.y - w.y)**2;
    if (l2 == 0) return Math.hypot(p.x - v.x, p.y - v.y);
    let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p.x - (v.x + t * (w.x - v.x)), p.y - (v.y + t * (w.y - v.y)));
}

const keys = {};
const p1 = new Car(110, 440, 0, { up: "ArrowUp", down: "ArrowDown", left: "ArrowLeft", right: "ArrowRight", ers: "ShiftRight" }, true);
const p2 = new Car(110, 460, 0, { up: "KeyW", down: "KeyS", left: "KeyA", right: "KeyD", ers: "Space" }, false);

window.addEventListener("keydown", (e) => {
    keys[e.code] = true;
    if (e.key === "Shift") keys["ShiftRight"] = true;

    if (gameState === "SELECT") {
        if (e.code === "ArrowUp") p1TeamIdx = (p1TeamIdx + 1) % TEAMS.length;
        if (e.code === "ArrowDown") p1TeamIdx = (p1TeamIdx - 1 + TEAMS.length) % TEAMS.length;
        if (e.code === "KeyW") p2TeamIdx = (p2TeamIdx + 1) % TEAMS.length;
        if (e.code === "KeyS") p2TeamIdx = (p2TeamIdx - 1 + TEAMS.length) % TEAMS.length;
        if (e.code === "KeyM") selectedSpeedIdx = (selectedSpeedIdx + 1) % SPEED_MODES.length;
    }
});

window.addEventListener("keyup", (e) => {
    keys[e.code] = false;
    if (e.key === "Shift") keys["ShiftRight"] = false;
});

function drawTrack() {
    // Barriers
    ctx.strokeStyle = "#888888";
    ctx.lineWidth = 66;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(trackCenter[0].x, trackCenter[0].y);
    for (let i = 1; i < trackCenter.length; i++) ctx.lineTo(trackCenter[i].x, trackCenter[i].y);
    ctx.closePath();
    ctx.stroke();

    // Red/White Kerbs
    ctx.strokeStyle = "#e10600";
    ctx.lineWidth = 62;
    ctx.setLineDash([12, 12]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Grass Runoff
    ctx.strokeStyle = "#27ae60";
    ctx.lineWidth = 58;
    ctx.stroke();

    // Asphalt
    ctx.strokeStyle = "#2c3e50";
    ctx.lineWidth = 48;
    ctx.stroke();

    // White Lines
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Finish Line Grid
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(310, 425);
    ctx.lineTo(310, 475);
    ctx.stroke();

    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
    ctx.font = "bold 34px Arial";
    ctx.textAlign = "center";
    ctx.fillText("SEPANG INTERNATIONAL CIRCUIT", canvas.width / 2, 270);
}

function drawHUD() {
    // P1 Telemetry Box
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.fillRect(10, 10, 210, 85);
    ctx.strokeStyle = p1.team.color;
    ctx.lineWidth = 2;
    ctx.strokeRect(10, 10, 210, 85);

    ctx.font = "bold 12px Arial";
    ctx.fillStyle = p1.team.color;
    ctx.textAlign = "left";
    ctx.fillText(`P1: ${p1.team.name}`, 20, 26);
    
    ctx.fillStyle = "#fff";
    let p1Kmh = Math.round(Math.abs(p1.speed) * 65);
    ctx.fillText(`KM/H: ${p1Kmh} | LAP: ${Math.min(p1.lap, p1.maxLaps)}/${p1.maxLaps}`, 20, 42);
    ctx.fillText(`TIME: ${formatTime(p1.currentLapTime)}`, 20, 58);
    ctx.fillStyle = "#fbc531";
    ctx.fillText(`BEST: ${formatTime(p1.bestLapTime)}`, 20, 74);

    // P1 ERS Bar
    ctx.fillStyle = "#333";
    ctx.fillRect(20, 80, 190, 6);
    ctx.fillStyle = p1.ersBoosting ? "#00f0ff" : p1.team.color;
    ctx.fillRect(20, 80, p1.ersBattery * 1.9, 6);

    // P2 Telemetry Box
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.fillRect(canvas.width - 220, 10, 210, 85);
    ctx.strokeStyle = p2.team.color;
    ctx.strokeRect(canvas.width - 220, 10, 210, 85);

    ctx.fillStyle = p2.team.color;
    ctx.textAlign = "right";
    ctx.fillText(`P2: ${p2.team.name}`, canvas.width - 20, 26);
    
    ctx.fillStyle = "#fff";
    let p2Kmh = Math.round(Math.abs(p2.speed) * 65);
    ctx.fillText(`KM/H: ${p2Kmh} | LAP: ${Math.min(p2.lap, p2.maxLaps)}/${p2.maxLaps}`, canvas.width - 20, 42);
    ctx.fillText(`TIME: ${formatTime(p2.currentLapTime)}`, canvas.width - 20, 58);
    ctx.fillStyle = "#fbc531";
    ctx.fillText(`BEST: ${formatTime(p2.bestLapTime)}`, canvas.width - 20, 74);

    // P2 ERS Bar
    ctx.fillStyle = "#333";
    ctx.fillRect(canvas.width - 210, 80, 190, 6);
    ctx.fillStyle = p2.ersBoosting ? "#00f0ff" : p2.team.color;
    ctx.fillRect(canvas.width - 210, 80, p2.ersBattery * 1.9, 6);
}

function drawUI() {
    ctx.textAlign = "center";

    if (gameState === "SELECT") {
        ctx.fillStyle = "rgba(0, 0, 0, 0.88)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = "#e10600";
        ctx.font = "bold 26px Arial";
        ctx.fillText("🏁 F1 2026 SEPANG GP (5 LAPS) 🏁", canvas.width / 2, 50);

        ctx.fillStyle = "#fbc531";
        ctx.font = "bold 15px Arial";
        ctx.fillText(`⚡ SPEED MODE: ${SPEED_MODES[selectedSpeedIdx].label} (Tekan 'M' Untuk Tukar)`, canvas.width / 2, 85);

        // P1 Box
        ctx.fillStyle = TEAMS[p1TeamIdx].color;
        ctx.fillRect(50, 110, 260, 240);
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 3;
        ctx.strokeRect(50, 110, 260, 240);

        ctx.fillStyle = "#fff";
        ctx.font = "bold 18px Arial";
        ctx.fillText("PLAYER 1", 180, 140);
        ctx.font = "14px Arial";
        ctx.fillText(`Team: ${TEAMS[p1TeamIdx].name}`, 180, 180);
        ctx.fillText(`Sponsor: ${TEAMS[p1TeamIdx].sponsor}`, 180, 210);
        ctx.font = "12px Arial";
        ctx.fillText("Guna ↑ / ↓ Untuk Tukar", 180, 310);

        // P2 Box
        ctx.fillStyle = TEAMS[p2TeamIdx].color;
        ctx.fillRect(370, 110, 260, 240);
        ctx.strokeRect(370, 110, 260, 240);

        ctx.fillStyle = "#fff";
        ctx.font = "bold 18px Arial";
        ctx.fillText("PLAYER 2", 500, 140);
        ctx.font = "14px Arial";
        ctx.fillText(`Team: ${TEAMS[p2TeamIdx].name}`, 500, 180);
        ctx.fillText(`Sponsor: ${TEAMS[p2TeamIdx].sponsor}`, 500, 210);
        ctx.font = "12px Arial";
        ctx.fillText("Guna W / S Untuk Tukar", 500, 310);

        ctx.fillStyle = "#4cd137";
        ctx.font = "bold 18px Arial";
        ctx.fillText("TEKAN SPACEBAR / CLICK UNTUK START RACE!", canvas.width / 2, 430);
    } else if (gameState === "GAMEOVER") {
        ctx.fillStyle = "rgba(0, 0, 0, 0.88)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = "#4cd137";
        ctx.font = "bold 32px Arial";
        ctx.fillText("🏁 CHEQUERED FLAG!", canvas.width / 2, 140);

        ctx.fillStyle = "#fbc531";
        ctx.font = "bold 24px Arial";
        ctx.fillText(`🏆 WINNER: ${winner}`, canvas.width / 2, 190);

        // Stats Summary
        ctx.fillStyle = "#FFF";
        ctx.font = "15px Arial";
        ctx.fillText(`P1 Best Lap: ${formatTime(p1.bestLapTime)}`, canvas.width / 2, 250);
        ctx.fillText(`P2 Best Lap: ${formatTime(p2.bestLapTime)}`, canvas.width / 2, 280);

        ctx.font = "14px Arial";
        ctx.fillText("Tekan SPACEBAR Untuk Kembali Ke Selection Menu", canvas.width / 2, 350);
    }
}

function startGame() {
    p1.setTeam(TEAMS[p1TeamIdx]);
    p2.setTeam(TEAMS[p2TeamIdx]);
    p1.reset();
    p2.reset();
    gameState = "PLAYING";
}

window.addEventListener("keydown", (e) => {
    if (e.code === "Space") {
        if (gameState === "SELECT") startGame();
        else if (gameState === "GAMEOVER") gameState = "SELECT";
    }
});

canvas.addEventListener("click", () => {
    if (gameState === "SELECT") startGame();
    else if (gameState === "GAMEOVER") gameState = "SELECT";
});

function loop(currentTime) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    drawTrack();

    p1.update(keys, currentTime);
    p2.update(keys, currentTime);

    p1.draw();
    p2.draw();

    if (gameState === "PLAYING") drawHUD();
    drawUI();

    requestAnimationFrame(loop);
}

requestAnimationFrame(loop);
</script>
</body>
</html>
"""

components.html(f1_2026_html, height=570)
