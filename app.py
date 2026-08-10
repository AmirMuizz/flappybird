import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="F1 Sepang 2-Player", page_icon="🏎️", layout="centered")

st.title("🏎️ F1 Sepang Circuit: 2 Player Battle")
st.caption("🏁 **P1 (Merah):** Arrow Keys + `Shift` (ERS) | **P2 (Biru):** WASD + `SPACE` (ERS)")

f1_game_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #1e272e;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            user-select: none;
            color: white;
        }
        #gameCanvas {
            border: 3px solid #ffdd59;
            border-radius: 10px;
            box-shadow: 0 6px 16px rgba(0,0,0,0.5);
            background: #2f3640;
        }
    </style>
</head>
<body>

<canvas id="gameCanvas" width="600" height="500"></canvas>

<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

let gameState = "START"; // START, PLAYING, GAMEOVER
let winner = "";

// Litar Sepang (Waypoints / Path)
const trackCenter = [
    {x: 100, y: 430}, // Main Straight Start
    {x: 480, y: 430}, // Main Straight End
    {x: 540, y: 380}, // T1 Outer
    {x: 500, y: 310}, // T2 Hairpin inner
    {x: 350, y: 310}, // Turn 3
    {x: 250, y: 220}, // Turn 5-6 S-Bends
    {x: 380, y: 150}, // Turn 7-8
    {x: 480, y: 80},  // Back Straight Start
    {x: 100, y: 80},  // Back Straight End
    {x: 60,  y: 200}, // Last Hairpin T15
    {x: 60,  y: 350}  // Back to Main Straight
];

class Car {
    constructor(x, y, angle, color, controls, name) {
        this.startX = x;
        this.startY = y;
        this.startAngle = angle;
        
        this.x = x;
        this.y = y;
        this.angle = angle;
        this.speed = 0;
        this.maxSpeed = 4.2;
        this.accel = 0.12;
        this.friction = 0.04;
        this.turnSpeed = 0.055;
        this.color = color;
        this.controls = controls;
        this.name = name;
        
        // ERS System
        this.ersBattery = 100; // 0 - 100 %
        this.ersBoosting = false;
        
        // Lap tracking
        this.lap = 1;
        this.maxLaps = 3;
        this.checkpoint = 0;
    }

    draw() {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.angle);

        // Badan Kereta F1 (Top View)
        ctx.fillStyle = this.color;
        // Main Body
        ctx.fillRect(-12, -5, 24, 10);
        // Front Wing
        ctx.fillStyle = "#111";
        ctx.fillRect(10, -7, 4, 14);
        // Rear Wing
        ctx.fillRect(-14, -6, 3, 12);
        // Wheels
        ctx.fillRect(-8, -8, 6, 3);
        ctx.fillRect(-8, 5, 6, 3);
        ctx.fillRect(4, -8, 6, 3);
        ctx.fillRect(4, 5, 6, 3);

        // ERS Flame Effect
        if (this.ersBoosting) {
            ctx.fillStyle = "#00d2d3";
            ctx.beginPath();
            ctx.arc(-16, 0, 4 + Math.random()*3, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.restore();
    }

    update(keys) {
        if (gameState !== "PLAYING") return;

        // Steering
        if (keys[this.controls.left]) this.angle -= this.turnSpeed * (this.speed / this.maxSpeed);
        if (keys[this.controls.right]) this.angle += this.turnSpeed * (this.speed / this.maxSpeed);

        // ERS Boost Button
        let currentMaxSpeed = this.maxSpeed;
        if (keys[this.controls.ers] && this.ersBattery > 0 && keys[this.controls.up]) {
            this.ersBoosting = true;
            currentMaxSpeed = 6.2; // ERS Top Speed
            this.ersBattery -= 0.6; // Consume battery
        } else {
            this.ersBoosting = false;
            if (this.ersBattery < 100 && this.speed < 2.0) {
                this.ersBattery += 0.25; // Recharge on braking/slow cornering
            }
        }

        // Acceleration & Braking
        if (keys[this.controls.up]) {
            if (this.speed < currentMaxSpeed) this.speed += this.accel;
        } else if (keys[this.controls.down]) {
            if (this.speed > -1.5) this.speed -= this.accel * 1.5;
        } else {
            if (this.speed > 0) this.speed -= this.friction;
            if (this.speed < 0) this.speed += this.friction;
            if (Math.abs(this.speed) < 0.05) this.speed = 0;
        }

        // Move
        this.x += Math.cos(this.angle) * this.speed;
        this.y += Math.sin(this.angle) * this.speed;

        // Checkpoints & Laps
        let targetCheck = trackCenter[this.checkpoint];
        let dist = Math.hypot(this.x - targetCheck.x, this.y - targetCheck.y);
        if (dist < 60) {
            this.checkpoint = (this.checkpoint + 1) % trackCenter.length;
            if (this.checkpoint === 1) { // Cross Finish Line
                this.lap++;
                if (this.lap > this.maxLaps) {
                    gameState = "GAMEOVER";
                    winner = this.name;
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

// Setup Cars & Controls
const keys = {};

const p1 = new Car(80, 420, 0, "#ff4d4d", {
    up: "ArrowUp", down: "ArrowDown", left: "ArrowLeft", right: "ArrowRight", ers: "ShiftRight"
}, "P1 (Merah)");

const p2 = new Car(80, 440, 0, "#00a8ff", {
    up: "KeyW", down: "KeyS", left: "KeyA", right: "KeyD", ers: "Space"
}, "P2 (Biru)");

// Extra keyboard support for Shift key P1
window.addEventListener("keydown", (e) => {
    keys[e.code] = true;
    if (e.key === "Shift") keys["ShiftRight"] = true;
});
window.addEventListener("keyup", (e) => {
    keys[e.code] = false;
    if (e.key === "Shift") keys["ShiftRight"] = false;
});

function drawTrack() {
    // Road/Asphalt
    ctx.strokeStyle = "#485460";
    ctx.lineWidth = 55;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(trackCenter[0].x, trackCenter[0].y);
    for (let i = 1; i < trackCenter.length; i++) {
        ctx.lineTo(trackCenter[i].x, trackCenter[i].y);
    }
    ctx.closePath();
    ctx.stroke();

    // Kerbs (Red/White stripes border)
    ctx.strokeStyle = "#ff4d4d";
    ctx.lineWidth = 58;
    ctx.setLineDash([15, 15]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Re-draw asphalt over kerbs
    ctx.strokeStyle = "#1e272e";
    ctx.lineWidth = 48;
    ctx.stroke();

    // Start / Finish Line
    ctx.strokeStyle = "#FFF";
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(300, 400);
    ctx.lineTo(300, 460);
    ctx.stroke();

    // Track Name Text
    ctx.fillStyle = "rgba(255, 255, 255, 0.15)";
    ctx.font = "bold 32px Arial";
    ctx.textAlign = "center";
    ctx.fillText("SEPANG F1 CIRCUIT", canvas.width / 2, 260);
}

function drawHUD() {
    // P1 HUD
    ctx.font = "bold 13px Arial";
    ctx.fillStyle = "#ff4d4d";
    ctx.textAlign = "left";
    ctx.fillText(`P1 Laps: ${Math.min(p1.lap, p1.maxLaps)}/${p1.maxLaps}`, 15, 25);
    // P1 ERS Bar
    ctx.fillStyle = "#333";
    ctx.fillRect(15, 32, 100, 10);
    ctx.fillStyle = p1.ersBoosting ? "#00d2d3" : "#ff4d4d";
    ctx.fillRect(15, 32, p1.ersBattery, 10);

    // P2 HUD
    ctx.fillStyle = "#00a8ff";
    ctx.textAlign = "right";
    ctx.fillText(`P2 Laps: ${Math.min(p2.lap, p2.maxLaps)}/${p2.maxLaps}`, canvas.width - 15, 25);
    // P2 ERS Bar
    ctx.fillStyle = "#333";
    ctx.fillRect(canvas.width - 115, 32, 100, 10);
    ctx.fillStyle = p2.ersBoosting ? "#00d2d3" : "#00a8ff";
    ctx.fillRect(canvas.width - 115, 32, p2.ersBattery, 10);

    // ERS Label
    ctx.fillStyle = "#00d2d3";
    ctx.font = "10px Arial";
    ctx.textAlign = "left";
    ctx.fillText("⚡ ERS (BOOST)", 15, 55);
    ctx.textAlign = "right";
    ctx.fillText("⚡ ERS (BOOST)", canvas.width - 15, 55);
}

function drawUI() {
    ctx.textAlign = "center";
    if (gameState === "START") {
        ctx.fillStyle = "rgba(0, 0, 0, 0.75)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = "#ffdd59";
        ctx.font = "bold 28px Arial";
        ctx.fillText("🏎️ SEPANG F1 GRAND PRIX", canvas.width / 2, 180);

        ctx.fillStyle = "#FFF";
        ctx.font = "14px Arial";
        ctx.fillText("P1 (Merah) : ARROW KEYS + SHIFT (ERS)", canvas.width / 2, 230);
        ctx.fillText("P2 (Biru)  : W A S D + SPACEBAR (ERS)", canvas.width / 2, 260);

        ctx.fillStyle = "#4cd137";
        ctx.font = "bold 16px Arial";
        ctx.fillText("TEKAN SPACEBAR / CLICK UNTUK START RACE!", canvas.width / 2, 320);
    } else if (gameState === "GAMEOVER") {
        ctx.fillStyle = "rgba(0, 0, 0, 0.8)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = "#4cd137";
        ctx.font = "bold 32px Arial";
        ctx.fillText("🏁 CHEQUERED FLAG!", canvas.width / 2, 180);

        ctx.fillStyle = "#ffdd59";
        ctx.font = "bold 24px Arial";
        ctx.fillText(`🏆 CHAMPION: ${winner}`, canvas.width / 2, 230);

        ctx.fillStyle = "#FFF";
        ctx.font = "14px Arial";
        ctx.fillText("Tekan SPACEBAR untuk Restart Race", canvas.width / 2, 290);
    }
}

// Start / Restart Handlers
window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && (gameState === "START" || gameState === "GAMEOVER")) {
        p1.reset();
        p2.reset();
        gameState = "PLAYING";
    }
});

canvas.addEventListener("click", () => {
    if (gameState === "START" || gameState === "GAMEOVER") {
        p1.reset();
        p2.reset();
        gameState = "PLAYING";
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

    drawHUD();
    drawUI();

    requestAnimationFrame(loop);
}

loop();
</script>
</body>
</html>
"""

components.html(f1_game_html, height=540)
