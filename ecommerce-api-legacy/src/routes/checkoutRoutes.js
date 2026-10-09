const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = ({ checkoutController }) => {
    const router = express.Router();
    router.post('/api/checkout', asyncHandler(checkoutController.checkout));
    return router;
};
