const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
    const proxy = createProxyMiddleware({
        target: process.env.SEMATIC_PROXY_OVERRIDE || 'http://127.0.0.1:5001',
        changeOrigin: true,
    });
    app.use('/api', proxy);
    app.use('/authenticate', proxy);
};
