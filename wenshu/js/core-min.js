/*
CryptoJS v3.1.2
code.google.com/p/crypto-js
(c) 2009-2013 by Jeff Mott. All rights reserved.
code.google.com/p/crypto-js/wiki/License
*/
var CryptoJS = CryptoJS || function(h, r) {
    var k = {},
        l = k.lib = {},
        n = function() {},
        f = l.Base = {
            extend: function(a) {
                n.prototype = this;
                var b = new n;
                a && b.mixIn(a);
                b.hasOwnProperty("init") || (b.init = function() {
                    b.$super.init.apply(this, arguments)
                });
                b.init.prototype = b;
                b.$super = this;
                return b
            },
            create: function() {
                var a = this.extend();
                a.init.apply(a, arguments);
                return a
            },
            init: function() {},
            mixIn: function(a) {
                for (var b in a)
                    a.hasOwnProperty(b) && (this[b] = a[b]);
                a.hasOwnProperty("toString") && (this.toString = a.toString)
            },
            clone: function() {
                return this.init.prototype.extend(this)
            }
        },
        j = l.WordArray = f.extend({
            init: function(a, b) {
                a = this.words = a || [];
                this.sigBytes = b != r ? b : 4 * a.length
            },
            toString: function(a) {
                return (a || s).stringify(this)
            },
            concat: function(a) {
                var b = this.words,
                    d = a.words,
                    c = this.sigBytes;
                a = a.sigBytes;
                this.clamp();
                if (c % 4)
                    for (var e = 0; e < a; e++)
                        b[c + e >>> 2] |= (d[e >>> 2] >>> 24 - 8 * (e % 4) & 255) << 24 - 8 * ((c + e) % 4);
                else if (65535 < d.length)
                    for (e = 0; e < a; e += 4)
                        b[c + e >>> 2] = d[e >>> 2];
                else
                    b.push.apply(b, d);
                this.sigBytes += a;
                return this
            },
            clamp: function() {
                var a = this.words,
                    b = this.sigBytes;
                a[b >>> 2] &= 4294967295 <<
                32 - 8 * (b % 4);
                a.length = h.ceil(b / 4)
            },
            clone: function() {
                var a = f.clone.call(this);
                a.words = this.words.slice(0);
                return a
            },
            random: function(a) {
                for (var b = [], d = 0; d < a; d += 4)
                    b.push(4294967296 * h.random() | 0);
                return new j.init(b, a)
            }
        }),
        m = k.enc = {},
        s = m.Hex = {
            stringify: function(a) {
                var b = a.words;
                a = a.sigBytes;
                for (var d = [], c = 0; c < a; c++) {
                    var e = b[c >>> 2] >>> 24 - 8 * (c % 4) & 255;
                    d.push((e >>> 4).toString(16));
                    d.push((e & 15).toString(16))
                }
                return d.join("")
            },
            parse: function(a) {
                for (var b = a.length, d = [], c = 0; c < b; c += 2)
                    d[c >>> 3] |= parseInt(a.substr(c,
                    2), 16) << 24 - 4 * (c % 8);
                return new j.init(d, b / 2)
            }
        },
        p = m.Latin1 = {
            stringify: function(a) {
                var b = a.words;
                a = a.sigBytes;
                for (var d = [], c = 0; c < a; c++)
                    d.push(String.fromCharCode(b[c >>> 2] >>> 24 - 8 * (c % 4) & 255));
                return d.join("")
            },
            parse: function(a) {
                for (var b = a.length, d = [], c = 0; c < b; c++)
                    d[c >>> 2] |= (a.charCodeAt(c) & 255) << 24 - 8 * (c % 4);
                return new j.init(d, b)
            }
        },
        t = m.Utf8 = {
            stringify: function(a) {
                try {
                    return decodeURIComponent(escape(p.stringify(a)))
                } catch (b) {
                    throw Error("Malformed UTF-8 data");
                }
            },
            parse: function(a) {
                return p.parse(unescape(encodeURIComponent(a)))
            }
        },
        q = l.BufferedBlockAlgorithm = f.extend({
            reset: function() {
                this._data = new j.init;
                this._nDataBytes = 0
            },
            _append: function(a) {
                "string" == typeof a && (a = t.parse(a));
                this._data.concat(a);
                this._nDataBytes += a.sigBytes
            },
            _process: function(a) {
                var b = this._data,
                    d = b.words,
                    c = b.sigBytes,
                    e = this.blockSize,
                    f = c / (4 * e),
                    f = a ? h.ceil(f) : h.max((f | 0) - this._minBufferSize, 0);
                a = f * e;
                c = h.min(4 * a, c);
                if (a) {
                    for (var g = 0; g < a; g += e)
                        this._doProcessBlock(d, g);
                    g = d.splice(0, a);
                    b.sigBytes -= c
                }
                return new j.init(g, c)
            },
            clone: function() {
                var a = f.clone.call(this);
                a._data = this._data.clone();
                return a
            },
            _minBufferSize: 0
        });
    l.Hasher = q.extend({
        cfg: f.extend(),
        init: function(a) {
            this.cfg = this.cfg.extend(a);
            this.reset()
        },
        reset: function() {
            q.reset.call(this);
            this._doReset()
        },
        update: function(a) {
            this._append(a);
            this._process();
            return this
        },
        finalize: function(a) {
            a && this._append(a);
            return this._doFinalize()
        },
        blockSize: 16,
        _createHelper: function(a) {
            return function(b, d) {
                return (new a.init(d)).finalize(b)
            }
        },
        _createHmacHelper: function(a) {
            return function(b, d) {
                return (new u.HMAC.init(a,
                d)).finalize(b)
            }
        }
    });
    var u = k.algo = {};
    return k
}(Math);

