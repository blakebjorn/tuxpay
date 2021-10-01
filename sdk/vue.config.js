const path = require("path")

// vue.config.js
module.exports = {
    filenameHashing: false,
    configureWebpack: {
        output: {
            filename: "tuxpay.js",
            path: path.resolve(__dirname, "dist"),
            libraryTarget: "var",
            library: "TuxPay"
        },
        optimization: {
            splitChunks: false
        },
    },
    css: {
        extract: false,
    },
    devServer: {
        proxy: {
            "/api/": {
                target: "http://localhost:8000",
            }
        }
    }
}