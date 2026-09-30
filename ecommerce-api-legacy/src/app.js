const express = require('express');
const config = require('./config');
const logger = require('./utils/logger');
const { createDatabase } = require('./database/connection');
const { initSchema } = require('./database/schema');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const PaymentService = require('./services/paymentService');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');
const checkoutRoutes = require('./routes/checkoutRoutes');
const adminRoutes = require('./routes/adminRoutes');
const userRoutes = require('./routes/userRoutes');
const requireAdminFactory = require('./middlewares/auth');
const errorHandler = require('./middlewares/errorHandler');

async function main() {
    const db = await createDatabase(config.dbFile);
    await initSchema(db, config);

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);
    const paymentService = new PaymentService({ gatewayKey: config.paymentGatewayKey });

    const checkoutController = new CheckoutController({
        db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService,
    });
    const reportController = new ReportController({ courseModel });
    const userController = new UserController({ db, userModel, enrollmentModel, paymentModel });

    if (!config.adminToken) logger.warn('ADMIN_TOKEN não definida; rotas administrativas responderão 401');
    const requireAdmin = requireAdminFactory(config);

    const app = express();
    app.use(express.json());
    app.use(checkoutRoutes(checkoutController));
    app.use(adminRoutes(reportController, requireAdmin));
    app.use(userRoutes(userController, requireAdmin));
    app.use(errorHandler);

    app.listen(config.port, () => {
        logger.info(`LMS API rodando na porta ${config.port}`);
    });
}

main().catch((err) => {
    logger.error('Falha ao iniciar a aplicação', err);
    process.exit(1);
});
