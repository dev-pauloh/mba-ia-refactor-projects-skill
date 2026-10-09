const express = require('express');
const config = require('./config');
const { createLogger } = require('./utils/logger');
const { Database } = require('./database/connection');
const { createSchema, seed } = require('./database/schema');
const { UserModel } = require('./models/userModel');
const { CourseModel } = require('./models/courseModel');
const { EnrollmentModel } = require('./models/enrollmentModel');
const { PaymentModel } = require('./models/paymentModel');
const { AuditLogModel } = require('./models/auditLogModel');
const { PaymentGateway } = require('./services/paymentGateway');
const { CheckoutService } = require('./services/checkoutService');
const { ReportService } = require('./services/reportService');
const { UserService } = require('./services/userService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createRequireAdmin } = require('./middlewares/auth');
const { createErrorHandler } = require('./middlewares/errorHandler');
const checkoutRoutes = require('./routes/checkoutRoutes');
const adminRoutes = require('./routes/adminRoutes');
const userRoutes = require('./routes/userRoutes');

async function main() {
    const logger = createLogger(config.logLevel);
    config.warnings.forEach((warning) => logger.warn(warning));
    if (!config.adminApiToken) logger.warn('ADMIN_API_TOKEN não definida; rotas administrativas responderão 401');

    const db = await Database.open(config.dbFile);
    await createSchema(db);
    await seed(db);

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);

    const paymentGateway = new PaymentGateway({ apiKey: config.paymentGatewayKey, logger });
    const checkoutService = new CheckoutService({
        db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway,
    });
    const reportService = new ReportService({ courseModel });
    const userService = new UserService({ db, userModel, enrollmentModel, paymentModel });

    const requireAdmin = createRequireAdmin({ adminApiToken: config.adminApiToken });

    const app = express();
    app.use(express.json());
    app.use(checkoutRoutes({ checkoutController: createCheckoutController({ checkoutService }) }));
    app.use(adminRoutes({ reportController: createReportController({ reportService }), requireAdmin }));
    app.use(userRoutes({ userController: createUserController({ userService }), requireAdmin }));
    app.use(createErrorHandler({ logger }));

    app.listen(config.port, () => {
        logger.info(`LMS API rodando na porta ${config.port}`);
    });
}

main().catch((err) => {
    process.stderr.write(`Falha ao iniciar a aplicação: ${err.stack}\n`);
    process.exit(1);
});
