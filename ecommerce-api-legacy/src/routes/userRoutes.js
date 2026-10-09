const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = ({ userController, requireAdmin }) => {
    const router = express.Router();
    router.delete('/api/users/:id', requireAdmin, asyncHandler(userController.remove));
    return router;
};
