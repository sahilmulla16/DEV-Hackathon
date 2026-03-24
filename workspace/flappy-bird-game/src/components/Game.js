import React, { useState, useEffect, useCallback } from 'react';
import './Game.css';

const Game = () => {
  const [birdPosition, setBirdPosition] = useState(250);
  const [pipes, setPipes] = useState([]);
  const [score, setScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [gameStarted, setGameStarted] = useState(false);

  const gameHeight = 500;
  const gravity = 5;
  const jump = 80;
  const pipeGap = 150;
  const pipeWidth = 60;
  const pipeSpeed = 3;

  const jumpBird = useCallback(() => {
    if (!gameStarted) {
      setGameStarted(true);
    }
    setBirdPosition((prev) => Math.max(prev - jump, 0));
  }, [gameStarted]);

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.code === 'Space') {
        jumpBird();
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [jumpBird]);

  useEffect(() => {
    if (!gameStarted || gameOver) return;

    const birdInterval = setInterval(() => {
      setBirdPosition((prev) => {
        const newPos = prev + gravity;
        if (newPos >= gameHeight - 30) {
          setGameOver(true);
        }
        return newPos;
      });
    }, 50);

    return () => clearInterval(birdInterval);
  }, [gameStarted, gameOver]);

  useEffect(() => {
    if (!gameStarted || gameOver) return;

    const pipeInterval = setInterval(() => {
      setPipes((prev) => {
        const newPipes = prev
          .map(pipe => ({ ...pipe, x: pipe.x - pipeSpeed }))
          .filter(pipe => pipe.x + pipeWidth > 0);

        const lastPipe = newPipes[newPipes.length - 1];
        if (!lastPipe || lastPipe.x < 300) {
          const topHeight = Math.floor(Math.random() * (gameHeight - pipeGap - 100)) + 50;
          newPipes.push({ x: 500, topHeight });
        }

        return newPipes;
      });
    }, 50);

    return () => clearInterval(pipeInterval);
  }, [gameStarted, gameOver]);

  useEffect(() => {
    if (!gameStarted || gameOver) return;

    const checkCollision = () => {
      for (let pipe of pipes) {
        if (pipe.x < 80 && pipe.x + pipeWidth > 50) {
          const bottomY = pipe.topHeight + pipeGap;
          if (birdPosition < pipe.topHeight || birdPosition + 30 > bottomY) {
            setGameOver(true);
          }
        }
        if (pipe.x + pipeWidth < 50 && pipe.x + pipeWidth >= 50 - pipeSpeed) {
          setScore(prev => prev + 1);
        }
      }
    };

    const collisionCheckInterval = setInterval(checkCollision, 10);
    return () => clearInterval(collisionCheckInterval);
  }, [pipes, birdPosition, gameStarted, gameOver]);

  const resetGame = () => {
    setBirdPosition(250);
    setPipes([]);
    setScore(0);
    setGameOver(false);
    setGameStarted(false);
  };

  return (
    <div className="game-container" onClick={gameOver ? resetGame : jumpBird}>
      <div className="game" style={{ height: gameHeight }}>
        <div
          className="bird"
          style={{
            position: 'absolute',
            left: '50px',
            top: `${birdPosition}px`,
            width: '30px',
            height: '30px',
            backgroundColor: 'yellow',
            borderRadius: '50%',
            border: '2px solid black',
          }}
        />
        {pipes.map((pipe, index) => (
          <React.Fragment key={index}>
            <div
              className="pipe top"
              style={{
                position: 'absolute',
                left: `${pipe.x}px`,
                top: '0px',
                width: `${pipeWidth}px`,
                height: `${pipe.topHeight}px`,
                backgroundColor: 'green',
              }}
            />
            <div
              className="pipe bottom"
              style={{
                position: 'absolute',
                left: `${pipe.x}px`,
                top: `${pipe.topHeight + pipeGap}px`,
                width: `${pipeWidth}px`,
                height: `${gameHeight - pipe.topHeight - pipeGap}px`,
                backgroundColor: 'green',
              }}
            />
          </React.Fragment>
        ))}
        <div className="score">Score: {score}</div>
        {gameOver && (
          <div className="game-over">
            <h2>Game Over</h2>
            <p>Final Score: {score}</p>
            <p>Click to Restart</p>
          </div>
        )}
        {!gameStarted && !gameOver && (
          <div className="start-screen">
            <h2>Flappy Bird</h2>
            <p>Click or press SPACE to start</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Game;