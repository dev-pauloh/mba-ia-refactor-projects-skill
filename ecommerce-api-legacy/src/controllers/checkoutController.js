const { validateCheckout } = require('../validators/checkoutValidator');

function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            const input = validateCheckout(req.body);
            const { enrollmentId } = await checkoutService.checkout(input);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };
