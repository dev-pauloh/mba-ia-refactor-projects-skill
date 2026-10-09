const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;

    const write = (name, stream) => (message, ...details) => {
        if (LEVELS[name] > threshold) return;
        const line = `${new Date().toISOString()} ${name.toUpperCase()} ${message}`;
        stream.write(details.length ? `${line} ${details.map(formatDetail).join(' ')}\n` : `${line}\n`);
    };

    return {
        error: write('error', process.stderr),
        warn: write('warn', process.stderr),
        info: write('info', process.stdout),
        debug: write('debug', process.stdout),
    };
}

function formatDetail(detail) {
    return detail instanceof Error ? detail.stack : String(detail);
}

module.exports = { createLogger };
