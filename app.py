import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit Flappy Bird", page_icon="🐤", layout="centered")

st.title("🐤 Flappy Bird in Streamlit")
st.caption("Press **Spacebar** or click/tap to jump and navigate between the pipes!")

# HTML5 Canvas + JavaScript Game Engine Engine
flappy_bird_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #70c5ce;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Arial', sans-serif;
            user-select: none;
        }
        #gameCanvas {
            border: 3px solid #333;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            background: #70c5ce;
        }
    </style>
</head>
<body>

<canvas id="gameCanvas" width="360" height="480"></canvas>

<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

// Game Variables
let frames = 0;
let score = 0;
let highScore = 0;
let gameState = "START"; // "START", "PLAYING", "GAMEOVER"

// Bird Properties
const bird = {
    x: 50,
    y: 150,
    radius: 12,
    gravity: 0.35,
    jump: 6.5,
    velocity: 0,
    
    draw() {
        ctx.fillStyle = "#FFD700";
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#000";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Eye
        ctx.fillStyle = "#FFF";
        ctx.beginPath();
        ctx.arc(this.x + 4, this.y - 4, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#000";
        ctx.beginPath();
        ctx.arc(this.x + 5, this.y - 4, 1.5, 0, Math.PI * 2);
        ctx.fill();

        // Beak
        ctx.fillStyle = "#FF4500";
        ctx.beginPath();
        ctx.moveTo(this.x + 8, this.y);
        ctx.lineTo(this.x + 16, this.y + 2);
        ctx.lineTo(this.x + 8, this.y + 6);
        ctx.closePath();
        ctx.fill();
    },
    
    flap() {
        this.velocity = -this.jump;
    },
    
    update() {
        this.velocity += this.gravity;
        this.y += this.velocity;

        // Ground Collision
        if (this.y + this.radius >= canvas.height - 40) {
            this.y = canvas.height - 40 - this.radius;
            gameState = "GAMEOVER";
        }
        
        // Ceiling Collision
        if (this.y - this.radius <= 0) {
            this.y = this.radius;
            this.velocity = 0;
        }
    },
    
    reset() {
        this.y = 150;
        this.velocity = 0;
    }
};

// Pipes Array
const pipes = {
    position: [],
    width: 50,
    gap: 120,
    dx: 2,

    draw() {
        ctx.fillStyle = "#2ecc71";
        ctx.strokeStyle = "#27ae60";
        ctx.lineWidth = 3;

        for (let p of this.position) {
            // Top Pipe
            ctx.fillRect(p.x, 0, this.width, p.top);
            ctx.strokeRect(p.x, 0, this.width, p.top);

            // Bottom Pipe
            let bottomY = p.top + this.gap;
            let bottomHeight = canvas.height - 40 - bottomY;
            ctx.fillRect(p.x, bottomY, this.width, bottomHeight);
            ctx.strokeRect(p.x, bottomY, this.width, bottomHeight);
        }
    },

    update() {
        if (frames % 100 === 0) {
            let maxTop = canvas.height - 40 - this.gap - 50;
            let minTop = 50;
            let topHeight = Math.floor(Math.random() * (maxTop - minTop + 1) + minTop);

            this.position.push({
                x: canvas.width,
                top: topHeight,
                passed: false
            });
        }

        for (let p of this.position) {
            p.x -= this.dx;

            // Collision Detection
            let birdLeft = bird.x - bird.radius;
            let birdRight = bird.x + bird.radius;
            let birdTop = bird.y - bird.radius;
            let birdBottom = bird.y + bird.radius;

            let pipeLeft = p.x;
            let pipeRight = p.x + this.width;
            let topPipeBottom = p.top;
            let bottomPipeTop = p.top + this.gap;

            if (birdRight > pipeLeft && birdLeft < pipeRight) {
                if (birdTop < topPipeBottom || birdBottom > bottomPipeTop) {
                    gameState = "GAMEOVER";
                }
            }

            // Score Tracking
            if (p.x + this.width < bird.x && !p.passed) {
                score++;
                p.passed = true;
                if (score > highScore) highScore = score;
            }
        }

        // Remove Offscreen Pipes
        if (this.position.length && this.position[0].x < -this.width) {
            this.position.shift();
        }
    },

    reset() {
        this.position = [];
    }
};

// Ground
function drawGround() {
    ctx.fillStyle = "#ded895";
    ctx.fillRect(0, canvas.height - 40, canvas.width, 40);
    ctx.fillStyle = "#73bf2e";
    ctx.fillRect(0, canvas.height - 40, canvas.width, 10);
}

// UI Overlays
function drawUI() {
    ctx.fillStyle = "#FFF";
    ctx.strokeStyle = "#000";
    ctx.lineWidth = 2;
    ctx.font = "bold 24px Arial";

    if (gameState === "PLAYING") {
        ctx.textAlign = "center";
        ctx.fillText(score, canvas.width / 2, 50);
        ctx.strokeText(score, canvas.width / 2, 50);
    } else if (gameState === "START") {
        ctx.textAlign = "center";
        ctx.fillText("FLAPPY BIRD", canvas.width / 2, 180);
        ctx.strokeText("FLAPPY BIRD", canvas.width / 2, 180);

        ctx.font = "16px Arial";
        ctx.fillText("Press Space or Click to Start", canvas.width / 2, 230);
    } else if (gameState === "GAMEOVER") {
        ctx.textAlign = "center";
        ctx.fillText("GAME OVER", canvas.width / 2, 180);
        ctx.strokeText("GAME OVER", canvas.width / 2, 180);

        ctx.font = "16px Arial";
        ctx.fillText(`Score: ${score}`, canvas.width / 2, 220);
        ctx.fillText(`Best: ${highScore}`, canvas.width / 2, 245);
        ctx.fillText("Press Space or Click to Restart", canvas.width / 2, 280);
    }
}

// Input Handlers
function action() {
    if (gameState === "START") {
        gameState = "PLAYING";
        bird.flap();
    } else if (gameState === "PLAYING") {
        bird.flap();
    } else if (gameState === "GAMEOVER") {
        bird.reset();
        pipes.reset();
        score = 0;
        frames = 0;
        gameState = "PLAYING";
    }
}

window.addEventListener("keydown", (e) => {
    if (e.code === "Space") {
        e.preventDefault();
        action();
    }
});

canvas.addEventListener("click", () => {
    action();
});

// Main Loop
function loop() {
    // Clear
    ctx.fillStyle = "#70c5ce";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (gameState === "PLAYING") {
        bird.update();
        pipes.update();
        frames++;
    }

    pipes.draw();
    drawGround();
    bird.draw();
    drawUI();

    requestAnimationFrame(loop);
}

loop();
</script>
</body>
</html>
"""

# Render Component
components.html(flappy_bird_html, height=520)