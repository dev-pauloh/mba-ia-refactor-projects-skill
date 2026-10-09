const sqlite3 = require('sqlite3');

class Database {
    #conn;
    #transactionQueue = Promise.resolve();

    constructor(conn) {
        this.#conn = conn;
    }

    static open(filename) {
        return new Promise((resolve, reject) => {
            const conn = new sqlite3.Database(filename, (err) => (err ? reject(err) : resolve(new Database(conn))));
        });
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.#conn.run(sql, params, function onRun(err) {
                if (err) reject(err);
                else resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.#conn.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.#conn.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.#conn.exec(sql, (err) => (err ? reject(err) : resolve()));
        });
    }

    // Transações são serializadas: a conexão SQLite é única e não suporta BEGIN aninhado.
    transaction(work) {
        const result = this.#transactionQueue.then(async () => {
            await this.run('BEGIN');
            try {
                const value = await work();
                await this.run('COMMIT');
                return value;
            } catch (err) {
                await this.run('ROLLBACK');
                throw err;
            }
        });
        this.#transactionQueue = result.catch(() => {});
        return result;
    }

    close() {
        return new Promise((resolve, reject) => {
            this.#conn.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

module.exports = { Database };
