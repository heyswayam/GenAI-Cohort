import React, { useState } from 'react';
import './Calculator.css';

const BUTTONS = [
  'AC', '+/-', '%', '÷',
  '7', '8', '9', '×',
  '4', '5', '6', '-',
  '1', '2', '3', '+',
  '0', '.', '='
];

function Calculator() {
  const [display, setDisplay] = useState('0');
  const [operator, setOperator] = useState(null);
  const [firstNum, setFirstNum] = useState(null);
  const [waitingForSecondNum, setWaitingForSecondNum] = useState(false);

  const calculate = (n1, n2, op) => {
    switch (op) {
      case '+':
        return n1 + n2;
      case '-':
        return n1 - n2;
      case '×':
        return n1 * n2;
      case '÷':
        if (n2 === 0) {
          return 'Error';
        }
        return n1 / n2;
      default:
        return n2;
    }
  };

  const handleButtonClick = (value) => {
    if (value === 'AC') {
      setDisplay('0');
      setOperator(null);
      setFirstNum(null);
      setWaitingForSecondNum(false);
      return;
    }

    if (value === '+/-') {
      if (display !== '0') {
        setDisplay((parseFloat(display) * -1).toString());
      }
      return;
    }

    if (value === '%') {
      setDisplay((parseFloat(display) / 100).toString());
      return;
    }

    if (['+', '-', '×', '÷'].includes(value)) {
      if (operator && waitingForSecondNum) {
        // Replace operator if user pressed operator consecutively
        setOperator(value);
        return;
      }
      if (firstNum == null) {
        setFirstNum(parseFloat(display));
      } else if (!waitingForSecondNum) {
        const result = calculate(firstNum, parseFloat(display), operator);
        setDisplay(result.toString());
        setFirstNum(result);
      }
      setOperator(value);
      setWaitingForSecondNum(true);
      return;
    }

    if (value === '=') {
      if (operator && !waitingForSecondNum) {
        const result = calculate(firstNum, parseFloat(display), operator);
        setDisplay(result.toString());
        setFirstNum(null);
        setOperator(null);
        setWaitingForSecondNum(false);
      }
      return;
    }

    // Number or dot input
    if (waitingForSecondNum) {
      setDisplay(value === '.' ? '0.' : value);
      setWaitingForSecondNum(false);
    } else {
      if (value === '.' && display.includes('.')) {
        return;
      }
      setDisplay(display === '0' && value !== '.' ? value : display + value);
    }
  };

  return (
    <div className="calculator">
      <div className="display" data-testid="display">{display}</div>
      <div className="buttons">
        {BUTTONS.map((btn, idx) => (
          <button
            key={idx}
            className={`button ${btn === '0' ? 'zero' : ''} ${btn === '=' ? 'equals' : ''}`}
            onClick={() => handleButtonClick(btn)}
            aria-label={`Calculator button ${btn}`}
          >
            {btn}
          </button>
        ))}
      </div>
    </div>
  );
}

export default Calculator;
