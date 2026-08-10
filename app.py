import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="F1 2026 Sepang GP", page_icon="🏎️", layout="centered")

st.title("🏎️ F1 2026 Sepang Grand Prix")
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

<canvas id="gameCanvas" width="650" height="520"></canvas>

<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

// Game States: "SELECT", "PLAYING", "GAMEOVER"
let gameState = "SELECT"; 
let winner = "";

// Senarai Pasukan F1 2026 & Penaja
const TEAMS = [
    { name: "Oracle Red Bull", color: "#0600ef", accent: "#fcd116", sponsor: "ORACLE" },
    { name: "Scuderia Ferrari", color: "#e8002d", accent: "#ffffff", sponsor: "SHELL" },
    { name: "Mercedes-AMG", color: "#00a29c", accent: "#000000", sponsor: "PETRONAS" },
    { name: "McLaren F1", color: "#ff8000", accent: "#0090ff", sponsor: "ANDROID" },
    { name: "Aston Martin", color: "#229971", accent: "#cedc00", sponsor: "ARAMCO" },
    { name: "Alpine F1", color: "#0093cc", accent: "#ff69b4", sponsor: "BWT" }
];

// Tetapan Kelajuan Litar
const SPEED_MODES = [
    { label: "NORMAL", topSpeed: 3.5, accel: 0.08, ersSpeed: 5.0 },
    { label: "FAST ⚡", topSpeed: 4.5, accel: 0.12, ersSpeed: 6.2 },
    { label: "TURBO 🔥", topSpeed: 5.5, accel: 0.16, ersSpeed: 7.5 }
];
let selectedSpeedIdx = 1; // Default Fast

let p1TeamIdx = 0;
let p2TeamIdx = 1;

// Waypoints Litar Sepang
const trackCenter = [
    {x: 120, y: 440}, // Main Straight
    {x: 520, y: 440}, 
    {x: 580, y: 390}, // T1 Outer
    {x: 530, y: 310}, // T2 Hairpin
    {x: 380, y: 310}, // Turn 3
    {x: 270, y: 220}, // S-Bends T5-6
    {x: 400, y: 140}, // Turn 7-8
    {x: 520, y: 80},  // Back Straight
    {x: 120, y: 80},  
    {x: 70,  y: 200}, // Last Hairpin T15
    {x: 70,  y: 360}  
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
        
        // ERS Battery System
        this.ersBattery = 100;
        this.ersBoosting = false;
        
        this.lap = 1;
        this.maxLaps = 3;
        this.checkpoint = 0;
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

        // Body Chassis
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

        // ERS Flame Burst
        if (this.ersBoosting) {
            ctx.fillStyle = "#00f0ff";
            ctx.beginPath();
            ctx.arc(-18, 0, 4 + Math.random()*4, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.restore();
    }

    update(keys) {
        if (gameState !== "PLAYING") return;

        let spdMode = SPEED_MODES[selectedSpeedIdx];

        // Semak lokasi track (Gravel/Grass Check)
        let isOnTrack = false;
        for (let i = 0; i < trackCenter.length - 1; i++) {
            let p1 = trackCenter[i];
            let p2 = trackCenter[i+1];
            if (distToSegment({x: this.x, y: this.y}, p1, p2) < 28) {
                isOnTrack = true;
                break;
            }
        }

        // Penalti Off-Track (Pagar/Rumput)
        let maxAllowedSpeed = isOnTrack ? spdMode.topSpeed : 1.0;
        let accelRate = spdMode.accel;
        let brakeRate = 0.15;
        let friction = 0.04;

        // Stereng Adaptif (Responsif bila perlahan, stabil bila laju)
        let turnRatio = Math.min(1.2, Math.max(0.3, Math.abs(this.speed) / spdMode.topSpeed));
        let turnSpeed = 0.052 * turnRatio;

        if (keys[this.controls.left]) this.angle -= turnSpeed;
        if (keys[this.controls.right]) this.angle += turnSpeed;

        // ERS Boost System
        if (keys[this.controls.ers] && this.ersBattery > 0 && keys[this.controls.up] && isOnTrack) {
            this.ersBoosting = true;
            maxAllowedSpeed = spdMode.ersSpeed;
            accelRate = spdMode.accel * 1.5;
            this.ersBattery -= 0.6;
        } else {
            this.ersBoosting = false;
            if (this.ersBattery < 100 && this.speed < 2.0) {
                this.ersBattery += 0.25; // Cas bateri bila brek/slow
            }
        }

        // Kawalan Gas & Brek Dinamik
        if (keys[this.controls.up]) {
            if (this.speed < maxAllowedSpeed) this.speed += accelRate;
            else this.speed -= friction;
        } else if (keys[this.controls.down]) {
            if (this.speed > -1.2) this.speed -= brakeRate; // Brek tajam
        } else {
            if (this.speed > 0) this.speed -= friction;
            if (this.speed < 0) this.speed += friction;
            if (Math.abs(this.speed) < 0.05) this.speed = 0;
        }

        // Pergerakan Kereta
        this.x += Math.cos(this.angle) * this.speed;
        this.y += Math.sin(this.angle) * this.speed;

        // Checkpoints & Laps
        let targetCheck = trackCenter[this.checkpoint];
        let dist = Math.hypot(this.x - targetCheck.x, this.y - targetCheck.y);
        if (dist < 55) {
            this.checkpoint = (this.checkpoint + 1) % trackCenter.length;
            if (this.checkpoint === 1) {
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
    }
}

function distToSegment(p, v, w) {
    let l2 = (v.x - w.x)**2 + (v.y - w.y)**2;
    if (l2 == 0) return Math.hypot(p.x - v.x, p.y - v.y);
    let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p.x - (v.x + t * (w.x - v.x)), p.y - (v.y + t * (w.y - v.y)));
}

const keys = {};
const p1 = new Car(100, 430, 0, { up: "ArrowUp", down: "ArrowDown", left: "ArrowLeft", right: "ArrowRight", ers: "ShiftRight" }, true);
const p2 = new Car(100, 450, 0, { up: "KeyW", down: "KeyS", left: "KeyA", right: "KeyD", ers: "Space" }, false);

window.addEventListener("keydown", (e) => {
    keys[e.code] = true;
    if (e.key === "Shift") keys["ShiftRight"] = true;

    if (gameState === "SELECT") {
        if (e.code === "ArrowUp") p1TeamIdx = (p1TeamIdx + 1) % TEAMS.length;
        if (e.code === "ArrowDown") p1TeamIdx = (p1TeamIdx - 1 + TEAMS.length) % TEAMS.length;
        if (e.code === "KeyW") p2TeamIdx = (p2TeamIdx + 1) % TEAMS.length;
        if (e.code === "KeyS") p2TeamIdx = (p2TeamIdx - 1 + TEAMS.length) % TEAMS.length;
        
        // Tukar Mode Kelajuan (Kekunci M)
        if (e.code === "KeyM") selectedSpeedIdx = (selectedSpeedIdx + 1) % SPEED_MODES.length;
    }
});

window.addEventListener("keyup", (e) => {
    keys[e.code] = false;
    if (e.key === "Shift") keys["ShiftRight"] = false;
});

function drawTrack() {
    // Pagar & Guard Rail
    ctx.strokeStyle = "#888888";
    ctx.lineWidth = 66;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(trackCenter[0].x, trackCenter[0].y);
    for (let i = 1; i < trackCenter.length; i++) ctx.lineTo(trackCenter[i].x, trackCenter[i].y);
    ctx.closePath();
    ctx.stroke();

    // Red & White Barriers
    ctx.strokeStyle = "#e10600";
    ctx.lineWidth = 62;
    ctx.setLineDash([12, 12]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Grass Runoff
    ctx.strokeStyle = "#27ae60";
    ctx.lineWidth = 58;
    ctx.stroke();

    // Asphalt Track
    ctx.strokeStyle = "#2c3e50";
    ctx.lineWidth = 48;
    ctx.stroke();

    // White Border Lines
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Finish Line Grid
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(300, 415);
    ctx.lineTo(300, 465);
    ctx.stroke();

    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
    ctx.font = "bold 32px Arial";
    ctx.textAlign = "center";
    ctx.fillText("SEPANG INTERNATIONAL CIRCUIT", canvas.width / 2, 270);
}

function drawHUD() {
    ctx.font = "bold 13px Arial";

    // P1 HUD
    ctx.fillStyle = p1.team.color;
    ctx.textAlign = "left";
    let p1Spd = Math.round(Math.abs(p1.speed) * 60);
    ctx.fillText(`P1: ${p1.team.name} | ${p1Spd} KM/H | Lap: ${Math.min(p1.lap, p1.maxLaps)}/${p1.maxLaps}`, 15, 25);
    ctx.fillStyle = "#333";
    ctx.fillRect(15, 32, 110, 10);
    ctx.fillStyle = p1.ersBoosting ? "#00f0ff" : p1.team.color;
    ctx.fillRect(15, 32, p1.ersBattery * 1.1, 10);

    // P2 HUD
    ctx.fillStyle = p2.team.color;
    ctx.textAlign = "right";
    let p2Spd = Math.round(Math.abs(p2.speed) * 60);
    ctx.fillText(`P2: ${p2.team.name} | ${p2Spd} KM/H | Lap: ${Math.min(p2.lap, p2.maxLaps)}/${p2.maxLaps}`, canvas.width - 15, 25);
    ctx.fillStyle = "#333";
    ctx.fillRect(canvas.width - 125, 32, 110, 10);
    ctx.fillStyle = p2.ersBoosting ? "#00f0ff" : p2.team.color;
    ctx.fillRect(canvas.width - 125, 32, p2.ersBattery * 1.1, 10);

    // ERS Labels
    ctx.fillStyle = "#00f0ff";
    ctx.font = "10px Arial";
    ctx.textAlign = "left";
    ctx.fillText("⚡ ERS BOOST", 15, 55);
    ctx.textAlign = "right";
    ctx.fillText("⚡ ERS BOOST", canvas.width - 15, 55);
}

function drawUI() {
    ctx.textAlign = "center";

    if (gameState === "SELECT") {
        ctx.fillStyle = "rgba(0, 0, 0, 0.88)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = "#e10600";
        ctx.font = "bold 26px Arial";
        ctx.fillText("🏁 F1 2026 TEAM SELECTION 🏁", canvas.width / 2, 50);

        // Speed Mode Indicator
        ctx.fillStyle = "#fbc531";
        ctx.font = "bold 15px Arial";
        ctx.fillText(`⚡ TETAPAN KELAJUAN: ${SPEED_MODES[selectedSpeedIdx].label} (Tekan 'M' Untuk Tukar)`, canvas.width / 2, 85);

        // P1 Selection Box
        ctx.fillStyle = TEAMS[p1TeamIdx].color;
        ctx.fillRect(40, 110, 250, 230);
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 3;
        ctx.strokeRect(40, 110, 250, 230);

        ctx.fillStyle = "#fff";
        ctx.font = "bold 18px Arial";
        ctx.fillText("PLAYER 1", 165, 140);
        ctx.font = "14px Arial";
        ctx.fillText(`Team: ${TEAMS[p1TeamIdx].name}`, 165, 180);
        ctx.fillText(`Sponsor: ${TEAMS[p1TeamIdx].sponsor}`, 165, 210);
        ctx.font = "12px Arial";
        ctx.fillText("Guna ↑ / ↓ Untuk Tukar", 165, 300);

        // P2 Selection Box
        ctx.fillStyle = TEAMS[p2TeamIdx].color;
        ctx.fillRect(360, 110, 250, 230);
        ctx.strokeRect(360, 110, 250, 230);

        ctx.fillStyle = "#fff";
        ctx.font = "bold 18px Arial";
        ctx.fillText("PLAYER 2", 485, 140);
        ctx.font = "14px Arial";
        ctx.fillText(`Team: ${TEAMS[p2TeamIdx].name}`, 485, 180);
        ctx.fillText(`Sponsor: ${TEAMS[p2TeamIdx].sponsor}`, 485, 210);
        ctx.font = "12px Arial";
        ctx.fillText("Guna W / S Untuk Tukar", 485, 300);

        ctx.fillStyle = "#4cd137";
        ctx.font = "bold 18px Arial";
        ctx.fillText("TEKAN SPACEBAR / CLICK UNTUK START RACE!", canvas.width / 2, 420);
    } else if (gameState === "GAMEOVER") {
        ctx.fillStyle = "rgba(0, 0, 0, 0.85)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = "#4cd137";
        ctx.font = "bold 32px Arial";
        ctx.fillText("🏁 CHEQUERED FLAG!", canvas.width / 2, 180);

        ctx.fillStyle = "#fbc531";
        ctx.font = "bold 24px Arial";
        ctx.fillText(`🏆 WINNER: ${winner}`, canvas.width / 2, 240);

        ctx.fillStyle = "#FFF";
        ctx.font = "14px Arial";
        ctx.fillText("Tekan SPACEBAR Untuk Kembali Ke Selection Menu", canvas.width / 2, 310);
    }
}

// Start / Restart Actions
window.addEventListener("keydown", (e) => {
    if (e.code === "Space") {
        if (gameState === "SELECT") {
            p1.setTeam(TEAMS[p1TeamIdx]);
            p2.setTeam(TEAMS[p2TeamIdx]);
            p1.reset();
            p2.reset();
            gameState = "PLAYING";
        } else if (gameState === "GAMEOVER") {
            gameState = "SELECT";
        }
    }
});

canvas.addEventListener("click", () => {
    if (gameState === "SELECT") {
        p1.setTeam(TEAMS[p1TeamIdx]);
        p2.setTeam(TEAMS[p2TeamIdx]);
        p1.reset();
        p2.reset();
        gameState = "PLAYING";
    } else if (gameState === "GAMEOVER") {
        gameState = "SELECT";
    }
});

// Main 60 FPS Game Loop
function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    drawTrack();

    p1.update(keys);
    p2.update(keys);

    p1.draw();
    p2.draw();

    if (gameState === "PLAYING") drawHUD();
    drawUI();

    requestAnimationFrame(loop);
}

loop();
</script>
</body>
</html>
"""

components.html(f1_2026_html, height=560)
