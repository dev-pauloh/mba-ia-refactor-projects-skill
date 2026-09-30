const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (checkoutController) => {
    const router = express.Router();

    router.post('/api/checkout', asyncHandler(async (req, res) => {
        const { usr, eml, pwd, c_id: courseId, card } = req.body || {};
        const result = await checkoutController.checkout({
            name: usr, email: eml, password: pwd, courseId, cardNumber: card,
        });
        res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
    }));

    return router;
};
