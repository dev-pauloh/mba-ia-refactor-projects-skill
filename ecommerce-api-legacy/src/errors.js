class AppError extends Error {
    constructor(message, statusCode = 500) {
        super(message);
        this.statusCode = statusCode;
    }
}

class ValidationError extends AppError {
    constructor(message) { super(message, 400); }
}

class UnauthorizedError extends AppError {
    constructor(message) { super(message, 401); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

class PaymentDeclinedError extends AppError {
    constructor(message) { super(message, 400); }
}

module.exports = { AppError, ValidationError, UnauthorizedError, NotFoundError, PaymentDeclinedError };
