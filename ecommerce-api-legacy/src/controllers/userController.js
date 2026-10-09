function createUserController({ userService }) {
    return {
        async remove(req, res) {
            await userService.deleteUser(req.params.id);
            res.send('Usuário deletado');
        },
    };
}

module.exports = { createUserController };
