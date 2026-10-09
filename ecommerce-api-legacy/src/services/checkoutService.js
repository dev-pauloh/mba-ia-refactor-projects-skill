const { PAYMENT_STATUS } = require('../config/constants');
const { NotFoundError, UnauthorizedError, PaymentDeclinedError } = require('../errors');
const { hashPassword, verifyPassword } = require('../utils/password');

class CheckoutService {
    constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway }) {
        Object.assign(this, { db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway });
    }

    async checkout({ name, email, password, courseId, cardNumber }) {
        const course = await this.courseModel.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const existingUser = await this.userModel.findByEmail(email);
        if (existingUser && !(await verifyPassword(password, existingUser.pass))) {
            throw new UnauthorizedError('Credenciais inválidas');
        }
        const passwordHash = existingUser ? null : await hashPassword(password);

        const status = await this.paymentGateway.charge({ cardNumber, amount: course.price });
        if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeclinedError();

        const enrollmentId = await this.db.transaction(async () => {
            const userId = existingUser ? existingUser.id : await this.userModel.create({ name, email, passwordHash });
            const newEnrollmentId = await this.enrollmentModel.create({ userId, courseId: course.id });
            await this.paymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status });
            await this.auditLogModel.record(`Checkout curso ${course.id} por ${userId}`);
            return newEnrollmentId;
        });

        return { enrollmentId };
    }
}

module.exports = { CheckoutService };
