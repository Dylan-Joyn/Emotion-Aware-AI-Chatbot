// ===================== app.js (full integration) =====================
// Goals:
// - Slack-style sending: Enter = Send, Shift+Enter = newline
// - Multi-conversation storage in localStorage
// - Robust init (no missing elements), safe storage, light perf guards

(() => {
    // ----------- Utilities & Guards -----------
    const CONVO_KEY = "chatui_convos_v2";
    const MAX_CONVOS = 50;           // simple cap to avoid unbounded growth
    const TYPING_STEP_TARGET = 80;    // chars per ~typing cycle
    const SUBMIT_THROTTLE_MS = 120;   // prevent rapid double-submits

    const now = () => Date.now();

    // UUID fallback for older browsers
    function uuid() {
        if (crypto && crypto.randomUUID) return crypto.randomUUID();
        // RFC4122-ish fallback
        return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
            const r = (Math.random() * 16) | 0;
            const v = c === "x" ? r : (r & 0x3) | 0x8;
            return v.toString(16);
        });
    }

    function safeParse(json, fallback) {
        try { return JSON.parse(json); } catch { return fallback; }
    }
    function loadConvos() {
        const raw = localStorage.getItem(CONVO_KEY);
        const arr = safeParse(raw, []);
        return Array.isArray(arr) ? arr : [];
    }
    function saveConvos() {
        try {
            localStorage.setItem(CONVO_KEY, JSON.stringify(convos.slice(0, MAX_CONVOS)));
        } catch (e) {
            // Storage full or blocked; degrade gracefully
            console.warn("localStorage save failed:", e);
        }
    }

    // ----------- DOM Ready init -----------
    document.addEventListener("DOMContentLoaded", init, { once: true });

    function init() {
        // Grab elements (guard against missing DOM)
        const convoList = document.getElementById("convoList");
        const messages = document.getElementById("messages");
        const form = document.getElementById("composer");
        const input = document.getElementById("input");

        if (!convoList || !messages || !form || !input) {
            console.error("Chat UI elements not found. Ensure script is loaded after HTML.");
            return;
        }

        // ----------- State -----------
        let convos = loadConvos();
        let activeId = (convos[0]?.id) || null;
        let lastSubmitAt = 0;

        // Ensure at least one conversation exists
        if (!convos.length) createConversation();

        // Initial render
        renderConvos();
        renderMessages();

        // ----------- Storage & Model ops -----------
        function createConversation(title = "New chat") {
            const id = uuid();
            const convo = {
                id,
                title,
                createdAt: now(),
                updatedAt: now(),
                messages: []
            };
            convos = [convo, ...convos].slice(0, MAX_CONVOS);
            activeId = id;
            saveConvos();
            renderConvos();
            renderMessages();
            return id;
        }

        function setActiveConversation(id) {
            activeId = id;
            renderConvos();
            renderMessages();
        }

        function renameConversation(id, title) {
            const c = convos.find(x => x.id === id);
            if (!c) return;
            c.title = (title || "").trim() || c.title;
            c.updatedAt = now();
            saveConvos();
            renderConvos();
        }

        function deleteConversation(id) {
            const i = convos.findIndex(x => x.id === id);
            if (i >= 0) {
                convos.splice(i, 1);
                if (activeId === id) activeId = convos[0]?.id || createConversation();
                saveConvos();
                renderConvos();
                renderMessages();
            }
        }

        function appendMessage(role, text) {
            const c = convos.find(x => x.id === activeId) || convos[0];
            if (!c) return;
            c.messages.push({
                id: uuid(),
                role,
                text,
                ts: now()
            });
            c.updatedAt = now();

            // Set title on first user message
            if (role === "user" && (!c.title || c.title === "New chat") && c.messages.length === 1) {
                const t = text.trim().replace(/\s+/g, " ").slice(0, 40);
                c.title = t || "New chat";
            }
            saveConvos();
        }

        // ----------- Rendering (with light perf guards) -----------
        function renderConvos() {
            if (!convos.length) { createConversation(); return; }

            const frag = document.createDocumentFragment();

            // New chat button
            const newBtn = document.createElement("div");
            newBtn.className = "convo";
            newBtn.id = "newChatBtn";
            newBtn.style.background = "#42352d";
            newBtn.style.border = "1px dashed rgba(255,217,168,0.25)";
            newBtn.textContent = "+ New chat";
            newBtn.addEventListener("click", () => createConversation());
            frag.appendChild(newBtn);

            convos.forEach(c => {
                const el = document.createElement("div");
                el.className = "convo";
                el.dataset.id = c.id;
                if (c.id === activeId) {
                    el.style.outline = "2px solid rgba(241,184,102,0.5)";
                }
                el.textContent = escapeHtml(c.title || "New chat");

                el.addEventListener("click", () => setActiveConversation(c.id));
                el.addEventListener("contextmenu", (e) => {
                    e.preventDefault();
                    if (confirm("Delete this conversation?")) deleteConversation(c.id);
                });

                frag.appendChild(el);
            });

            // Batch DOM update
            requestAnimationFrame(() => {
                convoList.innerHTML = "";
                convoList.appendChild(frag);
            });
        }

        function renderMessages() {
            const c = convos.find(x => x.id === activeId);
            if (!c) { messages.innerHTML = ""; return; }

            const frag = document.createDocumentFragment();
            for (const m of c.messages) {
                const div = document.createElement("div");
                div.className = "msg" + (m.role === "user" ? " me" : "");
                div.textContent = m.text;
                frag.appendChild(div);
            }

            // Batch DOM write
            requestAnimationFrame(() => {
                messages.innerHTML = "";
                messages.appendChild(frag);
                messages.scrollTop = messages.scrollHeight;
            });
        }

        function escapeHtml(s) {
            return String(s).replace(/[&<>"']/g, c => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
            }[c]));
        }

        // ----------- Composer: Slack-style Enter -----------
        input.addEventListener("keydown", (e) => {
            // Respect IME composition: don't send mid-composition
            if (e.isComposing) return;

            // Enter sends; Shift+Enter = newline
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                // throttle to avoid double-submit on key repeat
                const t = now();
                if (t - lastSubmitAt > SUBMIT_THROTTLE_MS) {
                    lastSubmitAt = t;
                    form.requestSubmit();
                }
            }
            // Shift+Enter falls through: browser inserts newline naturally
        });

        // Auto-resize (batched)
        input.addEventListener("input", debounceRAF(autoResize, 0));
        function autoResize() {
            input.style.height = "auto";
            input.style.height = Math.min(input.scrollHeight, window.innerHeight * 0.3) + "px";
        }

        // Focus composer with Ctrl/Cmd+K
        window.addEventListener("keydown", (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
                e.preventDefault();
                input.focus();
            }
        }, { passive: false });

        // Submit handler (drives echo for now)
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;

            appendMessage("user", text);
            addMessage(text, "me");

            input.value = "";
            autoResize();

            // Fake assistant response (replace with backend later)
            const reply = `Echoing: ${text}`;
            // Slight delay to simulate thinking
            setTimeout(() => {
                appendMessage("assistant", reply);
                streamBotReply(reply);
            }, 120);
        });

        // ----------- Message helpers -----------
        function addMessage(text, who = "bot") {
            const div = document.createElement("div");
            div.className = "msg" + (who === "me" ? " me" : "");
            div.textContent = text;
            // Batch append to avoid thrash on many quick sends
            requestAnimationFrame(() => {
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            });
        }

        function streamBotReply(fullText) {
            const div = document.createElement("div");
            div.className = "msg";
            messages.appendChild(div);

            let i = 0;
            const step = Math.max(2, Math.floor(fullText.length / TYPING_STEP_TARGET));
            const tick = () => {
                i += step;
                div.textContent = fullText.slice(0, i);
                messages.scrollTop = messages.scrollHeight;
                if (i < fullText.length) {
                    // Use rAF to align with paint and reduce jank
                    requestAnimationFrame(tick);
                }
            };
            requestAnimationFrame(tick);
        }

        // Pause any heavy UI loops when the tab is hidden (tiny power/CPU guard)
        document.addEventListener("visibilitychange", () => {
            // You can hook timers here if you later add any intervals.
            // For now, streamBotReply uses rAF which stops on hidden tabs automatically.
        });

        // ----------- Small helpers -----------
        function debounceRAF(fn, delayMs = 0) {
            let t = 0, rAF = 0;
            return (...args) => {
                if (t) clearTimeout(t);
                t = setTimeout(() => {
                    if (rAF) cancelAnimationFrame(rAF);
                    rAF = requestAnimationFrame(() => fn(...args));
                }, delayMs);
            };
        }
    }
})();
