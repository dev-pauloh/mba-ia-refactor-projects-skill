const { PaymentStatus } = require('../config/constants');
const { ValidationError, NotFoundError, PaymentDeclinedError } = require('../errors');
const { hashPassword } = require('../utils/password');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+$/;
const CARD_PATTERN = /^\d+$/;

function isNonEmptyString(value) {
    return typeof value === 'string' && value.trim() !== '';
}

function validateCheckout({ name, email, password, courseId, cardNumber }) {
    if (!name || !email || !courseId || !cardNumber) throw new ValidationError('Bad Request');
    if (!isNonEmptyString(name)) throw new ValidationError('Nome inválido');
    if (typeof email !== 'string' || !EMAIL_PATTERN.test(email)) throw new ValidationError('Email inválido');
    if (typeof cardNumber !== 'string' || !CARD_PATTERN.test(cardNumber)) throw new ValidationError('Cartão inválido');
    if (password !== undefined && password !== null && typeof password !== 'string') throw new ValidationError('Senha inválida');
    const id = Number(courseId);
    if (!Number.isInteger(id) || id <= 0) throw new ValidationError('Curso inválido');
    return { name: name.trim(), email: email.trim(), password, courseId: id, cardNumber };
}

class CheckoutController {
    constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService }) {
        Object.assign(this, { db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService });
    }

    async checkout(input) {
        const { name, email, password, courseId, cardNumber } = validateCheckout(input);

        const course = await this.courseModel.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const existingUser = await this.userModel.findByEmail(email);
        if (!existingUser && !isNonEmptyString(password)) {
            throw new ValidationError('Senha obrigatória para novo usuário');
        }

        const status = this.paymentService.charge(cardNumber, course.price);
        if (status !== PaymentStatus.PAID) throw new PaymentDeclinedError('Pagamento recusado');

        const enrollmentId = await this.db.transaction(async () => {
            const user = await this.userModel.findByEmail(email);
            const userId = user
                ? user.id
                : await this.userModel.create({ name, email, passwordHash: hashPassword(password) });
            const newEnrollmentId = await this.enrollmentModel.create({ userId, courseId });
            await this.paymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status });
            await this.auditLogModel.record(`Checkout curso ${courseId} por ${userId}`);
            return newEnrollmentId;
        });

        return { enrollmentId };
    }
}

module.exports = CheckoutController;
