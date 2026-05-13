/**
 * TorrStream ↔ Lampa position-sync plugin
 *
 * Push-installable Lampa plugin: subscribes to Lampa player events, writes
 * playback position back to a TorrStream wrapper, and resumes from the
 * server-side position when re-opening a torrent on any device.
 *
 * Install (inside Lampa):
 *   Settings → Расширения → Plugins → URL:
 *     https://tv.trikiman.shop/static/lampa-sync.js
 *
 * Override wrapper URL (optional, e.g. from a Lampa console):
 *   Lampa.Storage.set('torrstream_sync_url', 'https://example.com')
 *
 * The plugin only acts on TorrServer streams (URLs that match
 * `/stream/.*?link=<hash>&index=<idx>`). Anything else is ignored.
 */
(function () {
    'use strict';

    if (window.__torrstream_sync_loaded) return;
    window.__torrstream_sync_loaded = true;

    var DEFAULT_WRAPPER_URL = 'https://tv.trikiman.shop';
    var SAVE_INTERVAL_MS = 5000;
    var POLL_FOR_LAMPA_MS = 500;
    var POLL_FOR_LAMPA_TRIES = 60;

    function log() {
        try {
            var a = ['[torrstream-sync]'];
            for (var i = 0; i < arguments.length; i++) a.push(arguments[i]);
            console.log.apply(console, a);
        } catch (e) { /* noop */ }
    }

    function getWrapperUrl() {
        try {
            if (window.Lampa && Lampa.Storage && typeof Lampa.Storage.get === 'function') {
                var u = Lampa.Storage.get('torrstream_sync_url', '');
                if (u) return String(u).replace(/\/+$/, '');
            }
        } catch (e) { /* noop */ }
        return DEFAULT_WRAPPER_URL;
    }

    function parseStreamUrl(url) {
        if (!url || typeof url !== 'string') return null;
        try {
            var u = new URL(url, window.location.origin);
            if (!/\/stream\//.test(u.pathname)) return null;
            var hash = u.searchParams.get('link');
            var idxRaw = u.searchParams.get('index');
            if (!hash || idxRaw === null) return null;
            var idx = parseInt(idxRaw, 10);
            if (!isFinite(idx) || idx < 1) idx = 1;
            return { hash: hash, file_index: idx };
        } catch (e) { return null; }
    }

    function findVideo() {
        var vids = document.getElementsByTagName('video');
        for (var i = vids.length - 1; i >= 0; i--) {
            if (isFinite(vids[i].duration) && vids[i].duration > 0) return vids[i];
        }
        return vids.length ? vids[vids.length - 1] : null;
    }

    var current = null;       // { hash, file_index }
    var lastSavedAt = 0;
    var saveTimer = null;
    var resumeAttempted = false;

    function postPosition(state) {
        if (!current || !state) return;
        if (!isFinite(state.position) || state.position < 0) return;
        if (!isFinite(state.duration) || state.duration <= 0) return;
        var url = getWrapperUrl() + '/api/position/' + encodeURIComponent(current.hash);
        var body = JSON.stringify({
            file_index: current.file_index,
            position: Math.floor(state.position),
            duration: Math.floor(state.duration),
        });
        try {
            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: body,
                keepalive: true,
                mode: 'cors',
            }).catch(function () { /* noop */ });
        } catch (e) { /* noop */ }
        lastSavedAt = Date.now();
    }

    function tickSave() {
        if (!current) return;
        var v = findVideo();
        if (!v) return;
        if (!isFinite(v.duration) || v.duration <= 0) return;
        if (Date.now() - lastSavedAt < SAVE_INTERVAL_MS - 100) return;
        postPosition({ position: v.currentTime, duration: v.duration });
    }

    function flush() {
        if (!current) return;
        var v = findVideo();
        if (!v) return;
        if (!isFinite(v.duration) || v.duration <= 0) return;
        lastSavedAt = 0;
        postPosition({ position: v.currentTime, duration: v.duration });
    }

    function startTimer() {
        stopTimer();
        saveTimer = setInterval(tickSave, SAVE_INTERVAL_MS);
    }

    function stopTimer() {
        if (saveTimer) { clearInterval(saveTimer); saveTimer = null; }
    }

    function fetchResume(parsed) {
        var url = getWrapperUrl() + '/api/position/' + encodeURIComponent(parsed.hash) +
            '?file_index=' + encodeURIComponent(parsed.file_index);
        return fetch(url, { mode: 'cors' })
            .then(function (r) { return r.ok ? r.json() : null; })
            .catch(function () { return null; });
    }

    function tryResume(parsed) {
        if (resumeAttempted) return;
        resumeAttempted = true;
        fetchResume(parsed).then(function (data) {
            if (!data || !data.ok) {
                log('no saved position for', parsed);
                return;
            }
            var saved = parseInt(data.position, 10) || 0;
            if (saved < 10) {
                log('saved position too small to bother:', saved);
                return;
            }
            log('saved position:', saved, 'looking for video element to seek...');

            var seekedOnce = false;
            var attempts = 0;
            var maxAttempts = 240; // up to 60s — generous for slow streams
            var lastFightAt = 0;
            var lastFightCount = 0;

            function performSeek(v) {
                if (saved >= v.duration - 5) return false;
                try {
                    v.currentTime = saved;
                    seekedOnce = true;
                    log('seek -> ', saved, 'of', v.duration);
                    if (window.Lampa && Lampa.Noty && typeof Lampa.Noty.show === 'function') {
                        var mm = Math.floor(saved / 60);
                        var ss = String(Math.floor(saved % 60));
                        if (ss.length < 2) ss = '0' + ss;
                        Lampa.Noty.show('TorrStream: continued from ' + mm + ':' + ss);
                    }
                    return true;
                } catch (e) {
                    log('seek failed', e);
                    return false;
                }
            }

            var seeker = setInterval(function () {
                attempts++;
                if (!current || current.hash !== parsed.hash || current.file_index !== parsed.file_index) {
                    clearInterval(seeker);
                    return;
                }
                var v = findVideo();
                if (!v || !isFinite(v.duration) || v.duration <= 0) {
                    if (attempts > maxAttempts) clearInterval(seeker);
                    return;
                }

                if (!seekedOnce) {
                    // First seek: only if Lampa hasn't already restored to roughly the right time
                    if (Math.abs(v.currentTime - saved) > 5) {
                        performSeek(v);
                    } else {
                        log('Lampa already at correct position', v.currentTime, 'vs', saved);
                        seekedOnce = true;
                    }
                } else {
                    // Already seeked once. Watch for Lampa fighting us back to 0/stale.
                    // If currentTime drops near 0 within a few seconds of our seek, re-seek.
                    if (v.currentTime < Math.min(15, saved - 30) && lastFightCount < 3) {
                        var now = Date.now();
                        if (now - lastFightAt > 800) {
                            log('Lampa fought back to', v.currentTime, ' — re-seeking');
                            lastFightAt = now;
                            lastFightCount++;
                            performSeek(v);
                        }
                    }
                }

                if (attempts > maxAttempts) clearInterval(seeker);
            }, 250);
        });
    }

    function handleStart(url) {
        var parsed = parseStreamUrl(url);
        if (!parsed) {
            log('non-torrserver source, skip');
            return;
        }
        // Reset only when switching torrent/file
        if (!current || current.hash !== parsed.hash || current.file_index !== parsed.file_index) {
            resumeAttempted = false;
        }
        current = parsed;
        log('tracking', parsed);
        startTimer();
        tryResume(parsed);
    }

    function handleStop() {
        flush();
        stopTimer();
        current = null;
        resumeAttempted = false;
        log('stop');
    }

    // ---- Hooks ----------------------------------------------------------------

    function extractUrl(data) {
        if (!data || typeof data !== 'object') return '';
        return data.url ||
            data.player_video_url ||
            (data.movie && data.movie.url) ||
            (data.file && data.file.url) ||
            '';
    }

    function hookPlayerListener() {
        if (!(window.Lampa && Lampa.Listener && typeof Lampa.Listener.follow === 'function')) return false;
        if (Lampa.Listener.__torrstream_player_hooked) return true;
        Lampa.Listener.follow('player', function (e) {
            try {
                if (!e || !e.type) return;
                if (e.type === 'start') {
                    var url = extractUrl(e.data);
                    if (!url) {
                        var v = findVideo();
                        if (v && v.currentSrc) url = v.currentSrc;
                    }
                    handleStart(url);
                } else if (e.type === 'pause') {
                    flush();
                } else if (e.type === 'destroy' || e.type === 'ended') {
                    handleStop();
                }
            } catch (err) { log('player listener err', err); }
        });
        Lampa.Listener.__torrstream_player_hooked = true;
        return true;
    }

    function hookPlayMethod() {
        if (!(window.Lampa && Lampa.Player && typeof Lampa.Player.play === 'function')) return false;
        if (Lampa.Player.__torrstream_wrapped) return true;
        var orig = Lampa.Player.play;
        Lampa.Player.play = function (opts) {
            try {
                var url = '';
                if (opts && typeof opts === 'object') {
                    url = opts.url || (opts.movie && opts.movie.url) || '';
                }
                if (parseStreamUrl(url)) handleStart(url);
            } catch (e) { log('play wrapper err', e); }
            return orig.apply(this, arguments);
        };
        Lampa.Player.__torrstream_wrapped = true;
        return true;
    }

    function onVisibilityChange() {
        if (document.visibilityState === 'hidden') flush();
    }

    function registerLifecycleListeners() {
        // Registered exactly once even if attemptInit() polls many times.
        try {
            window.addEventListener('beforeunload', flush);
            window.addEventListener('pagehide', flush);
            document.addEventListener('visibilitychange', onVisibilityChange);
        } catch (e) { /* noop */ }
    }

    function attemptInit() {
        if (!window.Lampa) return false;
        var any = false;
        if (hookPlayerListener()) any = true;
        if (hookPlayMethod()) any = true;
        if (any) log('hooks installed (wrapper:', getWrapperUrl(), ')');
        return any;
    }

    registerLifecycleListeners();

    if (!attemptInit()) {
        var tries = 0;
        var poll = setInterval(function () {
            tries++;
            if (attemptInit() || tries > POLL_FOR_LAMPA_TRIES) clearInterval(poll);
        }, POLL_FOR_LAMPA_MS);
    }
})();
