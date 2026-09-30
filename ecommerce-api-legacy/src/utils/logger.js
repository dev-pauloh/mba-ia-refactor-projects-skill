function write(level, message) {
    const line = `${new Date().toISOString()} [${level}] ${message}`;
    if (level === 'ERROR') console.error(line);
    else if (level === 'WARN') console.warn(line);
    else console.info(line);
}

module.exports = {
    info: (message) => write('INFO', message),
    warn: (message) => write('WARN', message),
    error: (message, err) => write('ERROR', err ? `${message}: ${err.stack || err}` : message),
};
