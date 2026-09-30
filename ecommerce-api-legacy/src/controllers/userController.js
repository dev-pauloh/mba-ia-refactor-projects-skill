const { ValidationError, NotFoundError } = require('../errors');

class UserController {
    constructor({ db, userModel, enrollmentModel, paymentModel }) {
        Object.assign(this, { db, userModel, enrollmentModel, paymentModel });
    }

    async deleteUser(rawId) {
        const userId = Number(rawId);
        if (!Number.isInteger(userId) || userId <= 0) throw new ValidationError('Id de usuário inválido');

        await this.db.transaction(async () => {
            const user = await this.userModel.findById(userId);
            if (!user) throw new NotFoundError('Usuário não encontrado');
            await this.paymentModel.deleteByUserId(userId);
            await this.enrollmentModel.deleteByUserId(userId);
            await this.userModel.deleteById(userId);
        });
    }
}

module.exports = UserController;
