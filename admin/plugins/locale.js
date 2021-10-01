export default ({store, app}, inject) => {
    function currency(value, locale = null, _default = null) {
        if (typeof value === 'string' && !isNaN(parseFloat(value))) {
            value = parseFloat(value);
        }
        if (value === null || value === undefined) {
            return _default;
        }
        if (locale === null) {
            locale = store.state.locale ? store.state.locale : 'en-US';
        }
        // float = Math.round(float * 100) / 100 || 0.0;
        return value.toLocaleString((locale !== null ? locale : this.$store.state.locale), {
            style: "currency",
            currency: "CAD",
            currencyDisplay: 'symbol'
        }).replace(" US", "").replace("CA", "");
    }

    function date_string(value, options) {
        options = (options === undefined ? {} : options);
        let locale = (options.locale !== undefined ? options.locale : null);
        let _default = (options.default !== undefined ? options.default : null);
        let year = (options.year !== undefined ? options.year : true);
        let dow = (options.dow !== undefined ? options.dow : true);
        if (value === null || value === undefined) {
            return _default;
        }

        if (typeof value === 'number') {
            // 10000000000 corresponds to ~April 1970 - assume if the number is less than this that it is measured in seconds
            value = new Date((value < 10000000000 ? value * 1000 : value))
        } else if (typeof value === 'string') {
            value = new Date(value)
            value.setTime(value.getTime() + value.getTimezoneOffset() * 60 * 1000)
        }

        const fmt = {
            month: "short",
            day: "numeric",
        };
        if (dow) {
            fmt.dow = 'short';
        }
        if (year) {
            fmt.year = 'numeric';
        }
        return value.toLocaleDateString(locale || store.state.locale || this.$store.state.locale || 'en-US', fmt);
    }

    function time_string(value, locale = null, _default = null) {
        if (value === null || value === undefined) {
            return _default;
        }
        if (typeof value === 'number') {
            value = new Date(value)
        } else if (typeof value === 'string') {
            value = new Date(value)
            value.setTime(value.getTime() + value.getTimezoneOffset() * 60 * 1000)
        }
        return value.toLocaleTimeString(locale || store.state.locale || this.$store.state.locale || 'en-US');
    }

    function left_pad(x, len) {
        x = x.toString()
        while (x.length < len) {
            x = "0" + x
        }
        return x
    }

    inject('currency', currency);
    inject('left_pad', left_pad);
    inject('date_string', date_string);
    inject('time_string', time_string);
}
