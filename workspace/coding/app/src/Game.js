import React, { useRef, useEffect, useState } from 'react';

const Game = () => {
  const canvasRef = useRef(null);
  const [score, setScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationId;
    const gravity = 0.5;
    const jump = -7;
    let bird = { x: 50, y: 150, velocity: 0 };
    let pipes = [];
    let frame = 0;

    const pipeWidth = 50;
    const pipeGap = 150;

    const drawBird = () => {
      ctx.fillStyle = 'yellow';
      ctx.beginPath();
      ctx.arc(bird.x, bird.y, 20, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = 'black';
      ctx.beginPath();
      ctx.arc(bird.x + 10, bird.y - 5, 5, 0, Math.PI * 2);
      ctx.fill();
    };

    const drawPipes = () => {
      pipes.forEach(pipe => {
        ctx.fillStyle = 'green';
        ctx.fillRect(pipe.x, 0, pipeWidth, pipe.topHeight);
        ctx.fillRect(pipe.x, pipe.topHeight + pipeGap, pipeWidth, canvas.height - pipe.topHeight - pipeGap);
      });
    };

    const updatePipes = () => {
      if (frame % 100 === 0) {
        const topHeight = Math.random() * (canvas.height - pipeGap - 50) + 25;
        pipes.push({ x: canvas.width, topHeight });
      }

      pipes = pipes.filter(pipe => {
        pipe.x -= 2;
        if (pipe.x + pipeWidth < 0) return false;

        if (pipe.x < bird.x + 20 && pipe.x + pipeWidth > bird.x - 20) {
          if (bird.y - 20 < pipe.topHeight || bird.y + 20 > pipe.topHeight + pipeGap) {
            setGameOver(true);
          } else if (pipe.x === bird.x) {
            setScore(prev => prev + 1);
          }
        }
        return true;
      });
    };

    const gameLoop = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      bird.velocity += gravity;
      bird.y += bird.velocity;

      if (bird.y > canvas.height || bird.y < 0) {
        setGameOver(true);
      }

      updatePipes();
      drawBird();
      drawPipes();
      frame++;

      if (!gameOver) {
        animationId = requestAnimationFrame(gameLoop);
      }
    };

    const handleJump = () => {
      if (gameOver) return;
      bird.velocity = jump;
    };

    canvas.addEventListener('click', handleJump);

    gameLoop();

    return () => {
      canvas.removeEventListener('click', handleJump);
      cancelAnimationFrame(animationId);
    };
  }, [gameOver]);

  const resetGame = () => {
    setGameOver(false);
    setScore(0);
    // Restart effect
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  return (
    <div style={{ textAlign: 'center', fontFamily: 'Arial' }}>
      <h1>Flappy Bird</h1>
      <p>Score: {score}</p>
      <canvas
        ref={canvasRef}
        width="400"
        height="600"
        style={{ border: '1px solid black', marginTop: '20px' }}
      ></canvas>
      {gameOver && (
        <div>
          <p style={{ color: 'red', fontWeight: 'bold' }}>Game Over!</p>
          <button onClick={resetGame} style={{ padding: '10px 20px', fontSize: '16px' }}>Play Again</button>
        </div>
      )}
    </div>
  );
};

export default Game;