const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

let bird = {x: 50, y: 150, width: 20, height: 20, gravity: 0.5, lift: -9, velocity: 0};
let pipes = [];
let frame = 0;
let score = 0;

function drawBird() {
    ctx.fillStyle = 'yellow';
    ctx.fillRect(bird.x, bird.y, bird.width, bird.height);
}

function updateBird() {
    bird.velocity += bird.gravity;
    bird.y += bird.velocity;
    if (bird.y + bird.height >= canvas.height) {
        bird.y = canvas.height - bird.height;
        resetGame();
    }
}

function flap() {
    bird.velocity += bird.lift;
}

document.addEventListener('keydown', flap);

function createPipes() {
    if (frame % 75 === 0) {
        const gap = 100;
        const topHeight = Math.random() * (canvas.height - gap - 20);
        pipes.push({x: canvas.width, top: topHeight, bottom: canvas.height - (topHeight + gap)});
    }
}

function drawPipes() {
    ctx.fillStyle = 'green';
    pipes.forEach(pipe => {
        ctx.fillRect(pipe.x, 0, 40, pipe.top);
        ctx.fillRect(pipe.x, canvas.height - pipe.bottom, 40, pipe.bottom);
    });
}

function updatePipes() {
    pipes.forEach(pipe => {
        pipe.x -= 2;
        if (pipe.x + 40 < 0) {
            pipes.shift();
            score++;
        }
    });
}

function detectCollision() {
    pipes.forEach(pipe => {
        if (bird.x + bird.width > pipe.x && bird.x < pipe.x + 40) {
            if (bird.y < pipe.top || bird.y + bird.height > canvas.height - pipe.bottom) {
                resetGame();
            }
        }
    });
}

function resetGame() {
    bird.y = 150;
    bird.velocity = 0;
    pipes = [];
    score = 0;
}

function gameLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBird();
    updateBird();
    createPipes();
    drawPipes();
    updatePipes();
    detectCollision();
    frame++;
    requestAnimationFrame(gameLoop);
}

gameLoop();