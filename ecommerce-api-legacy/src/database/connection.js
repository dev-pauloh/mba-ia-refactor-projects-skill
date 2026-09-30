const sqlite3 = require('sqlite3');

class Database {
    constructor(filename) {
        this.conn = new sqlite3.Database(filename);
        this.queue = Promise.resolve();
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) =>
            this.conn.run(sql, params, function onRun(err) {
                if (err) reject(err);
                else resolve({ lastID: this.lastID, changes: this.changes });
            }));
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) =>
            this.conn.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) =>
            this.conn.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));
    }

    exec(sql) {
        return new Promise((resolve, reject) => this.conn.exec(sql, (err) => (err ? reject(err) : resolve())));
    }

    // Transações são serializadas: a conexão SQLite é única e compartilhada.
    transaction(fn) {
        const result = this.queue.then(async () => {
            await this.run('BEGIN');
            try {
                const value = await fn();
                await this.run('COMMIT');
                return value;
            } catch (err) {
                await this.run('ROLLBACK');
                throw err;
            }
        });
        this.queue = result.catch(() => {});
        return result;
    }

    close() {
        return new Promise((resolve, reject) => this.conn.close((err) => (err ? reject(err) : resolve())));
    }
}

async function createDatabase(filename) {
    const db = new Database(filename);
    await db.run('PRAGMA foreign_keys = ON');
    return db;
}

module.exports = { Database, createDatabase };
