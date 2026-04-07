// JavaScript sample file

function greet(name) {
  return `Hello, ${name}!`;
}

function calculateSum(numbers) {
  /*
   * Calculate sum of array
   * Returns the total
   */
  let sum = 0;
  for (let i = 0; i < numbers.length; i++) {
    sum += numbers[i];
  }
  return sum;
}

const result = greet('World');
console.log(result);
console.log(calculateSum([1, 2, 3, 4, 5]));
