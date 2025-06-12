public class Calculator {
    
    /**
     * Adds two integers
     */
    public int add(int a, int b) {
        return a + b;
    }
    
    /**
     * Subtracts two integers
     */
    public int subtract(int a, int b) {
        return a - b;
    }
    
    /**
     * Multiplies two integers
     */
    public int multiply(int a, int b) {
        return a * b;
    }
    
    /**
     * Divides two integers
     * @throws IllegalArgumentException if divisor is zero
     */
    public double divide(int dividend, int divisor) {
        if (divisor == 0) {
            throw new IllegalArgumentException("Division by zero is not allowed");
        }
        return (double) dividend / divisor;
    }
    
    /**
     * Calculates factorial of a number
     * @throws IllegalArgumentException if number is negative
     */
    public long factorial(int n) {
        if (n < 0) {
            throw new IllegalArgumentException("Factorial is not defined for negative numbers");
        }
        if (n == 0 || n == 1) {
            return 1;
        }
        return n * factorial(n - 1);
    }
    
    /**
     * Checks if a number is prime
     */
    public boolean isPrime(int number) {
        if (number <= 1) {
            return false;
        }
        if (number <= 3) {
            return true;
        }
        if (number % 2 == 0 || number % 3 == 0) {
            return false;
        }
        
        for (int i = 5; i * i <= number; i += 6) {
            if (number % i == 0 || number % (i + 2) == 0) {
                return false;
            }
        }
        return true;
    }
    
    /**
     * Calculates the power of a number
     */
    public double power(double base, int exponent) {
        return Math.pow(base, exponent);
    }
    
    /**
     * Calculates square root
     * @throws IllegalArgumentException if number is negative
     */
    public double sqrt(double number) {
        if (number < 0) {
            throw new IllegalArgumentException("Square root is not defined for negative numbers");
        }
        return Math.sqrt(number);
    }
} 