import React, { useState } from 'react';
import './Calculator.css';

const buttonLabels = [
  'AC', '+/-', '%', '÷',
  '7', '8', '9', '×',
  '4', '5', '6', '-',
  '1', '2', '3', '+',
  '0', '.', '='
];

const isOperator = (value: string) => ['÷', '×', '-', '+', '='].includes(value);

const Calculator: React.FC = () => {
  const [display, setDisplay] = useState('0');
  const [waitingForOperand, setWaitingForOperand] = useState(false);
  const [operator, setOperator] = useState<string | null>(null);
  const [operand, setOperand] = useState<number | null>(null);

  const inputDigit = (digit: string) => {
    if (waitingForOperand) {
      setDisplay(digit);
      setWaitingForOperand(false);
    } else {
      setDisplay(display === '0' ? digit : display + digit);
    }
  };

  const inputDot = () => {
    if (waitingForOperand) {
      setDisplay('0.');
      setWaitingForOperand(false);
    } else if (!display.includes('.')) {
      setDisplay(display + '.');
    }
  };

  const clearAll = () => {
    setDisplay('0');
    setOperand(null);
    setOperator(null);
    setWaitingForOperand(false);
  };

  const toggleSign = () => {
    const value = parseFloat(display);
    if (value !== 0) {
      setDisplay((value * -1).toString());
    }
  };

  const inputPercent = () => {
    const value = parseFloat(display);
    setDisplay((value / 100).toString());
  };

  const performOperation = (nextOperator: string) => {
    const inputValue = parseFloat(display);

    if (operand == null) {
      setOperand(inputValue);
    } else if (operator) {
      const currentValue = operand || 0;
      let result = currentValue;

      switch (operator) {
        case '+':
          result = currentValue + inputValue;
          break;
        case '-':
          result = currentValue - inputValue;
          break;
        case '×':
          result = currentValue * inputValue;
          break;
        case '÷':
          result = inputValue === 0 ? 0 : currentValue / inputValue;
          break;
      }

      setOperand(result);
      setDisplay(String(result));
    }

    setWaitingForOperand(true);
    setOperator(nextOperator === '=' ? null : nextOperator);
  };

  const handleClick = (label: string) => {
    if (label >= '0' && label <= '9') {
      inputDigit(label);
    } else if (label === '.') {
      inputDot();
    } else if (label === 'AC') {
      clearAll();
    } else if (label === '+/-') {
      toggleSign();
    } else if (label === '%') {
      inputPercent();
    } else if (isOperator(label)) {
      performOperation(label);
    }
  };

  return (
    <div className="calculator">
      <div className="display" data-testid="display">{display}</div>
      <div className="buttons">
        {buttonLabels.map((label, index) => (
          <button
            key={index}
            className={`button ${label === '0' ? 'zero' : ''} ${isOperator(label) ? 'operator' : ''}`}
            onClick={() => handleClick(label)}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default Calculator;
