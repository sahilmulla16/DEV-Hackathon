const TicTacToe = () => {
  const [board, setBoard] = React.useState(Array(9).fill(null));
  const [isXNext, setIsXNext] = React.useState(true);
  const [gameStatus, setGameStatus] = React.useState('Next player: X');

  const calculateWinner = (squares) => {
    const lines = [
      [0, 1, 2], [3, 4, 5], [6, 7, 8], // rows
      [0, 3, 6], [1, 4, 7], [2, 5, 8], // columns
      [0, 4, 8], [2, 4, 6] // diagonals
    ];
    for (let i = 0; i < lines.length; i++) {
      const [a, b, c] = lines[i];
      if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
        return squares[a];
      }
    }
    return squares.every(cell => cell !== null) ? 'Draw' : null;
  };

  const handleClick = (i) => {
    if (board[i] || calculateWinner(board)) return;

    const newBoard = board.slice();
    newBoard[i] = isXNext ? 'X' : 'O';
    setBoard(newBoard);
    const winner = calculateWinner(newBoard);

    if (winner === 'Draw') {
      setGameStatus('Game ended in a draw!');
    } else if (winner) {
      setGameStatus(`Winner: ${winner}`);
    } else {
      setIsXNext(!isXNext);
      setGameStatus(`Next player: ${isXNext ? 'O' : 'X'}`);
    }
  };

  const resetGame = () => {
    setBoard(Array(9).fill(null));
    setIsXNext(true);
    setGameStatus('Next player: X');
  };

  const renderCell = (i) => (
    <div className="cell" onClick={() => handleClick(i)}>
      {board[i]}
    </div>
  );

  return (
    <div>
      <h1>Tic Tac Toe</h1>
      <div className="status">{gameStatus}</div>
      <div className="board">
        {Array(9).fill(null).map((_, i) => renderCell(i))}
      </div>
      <button onClick={resetGame}>Reset Game</button>
    </div>
  );
};

ReactDOM.render(<TicTacToe />, document.getElementById('root'));