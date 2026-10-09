class UserService {
    constructor({ db, userModel, enrollmentModel, paymentModel }) {
        Object.assign(this, { db, userModel, enrollmentModel, paymentModel });
    }

    // Remove o usuário com suas matrículas e pagamentos, sem deixar órfãos.
    deleteUser(userId) {
        return this.db.transaction(async () => {
            await this.paymentModel.deleteByUserId(userId);
            await this.enrollmentModel.deleteByUserId(userId);
            return this.userModel.deleteById(userId);
        });
    }
}

module.exports = { UserService };
