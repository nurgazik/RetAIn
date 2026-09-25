import Foundation

/// Reader page for a piece: same CSS as src/generate.py, tap-to-reveal popup, and a
/// message to Swift on every highlight tap (so the tap reaches the served ledger).
enum PieceHTML {
    /// stats: word (lowercased) → [id, servings]; drives "Seen N times" and "Got it".
    static func page(title: String, label: String, body: String, attrib: String, stats: [String: [Int]] = [:]) -> String {
        let statsJSON = (try? String(data: JSONSerialization.data(withJSONObject: stats), encoding: .utf8)) ?? "{}"
        return """
        <!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body { font-family: Georgia, 'Times New Roman', serif; background: #faf8f4; color: #26221c;
                 margin: 0; padding: 1.25rem 1.25rem 4rem; line-height: 1.65; -webkit-text-size-adjust: 100%; }
          .kicker { font-family: -apple-system, sans-serif; font-size: .75rem; letter-spacing: .12em;
                    text-transform: uppercase; color: #8a6d3b; margin-bottom: .5rem; }
          h1 { font-size: 1.5rem; line-height: 1.25; margin: 0 0 1.25rem; }
          p { margin: 0 0 1.1rem; font-size: 1.06rem; }
          mark { background: linear-gradient(transparent 55%, #ffe08a 55%); padding: 0 .1em; border-radius: 2px; }
          .edited { text-decoration: underline; text-decoration-color: #e8c96a; text-decoration-thickness: 1.5px; text-underline-offset: 3px; }
          #pop { position: absolute; display: none; z-index: 10; max-width: 280px; padding: .6rem .8rem;
                 background: #26221c; color: #faf8f4; border-radius: 8px; font-family: -apple-system, sans-serif;
                 font-size: .85rem; line-height: 1.45; }
          #pop b { color: #ffd76e; }
          #pop .meta { display: block; margin-top: .4rem; font-size: .75rem; opacity: .8; }
          #pop button { margin-top: .5rem; font: inherit; font-size: .8rem; padding: .3rem .7rem; border: 0;
                        border-radius: 6px; background: #ffd76e; color: #26221c; }
          #pop button:disabled { opacity: .6; }
          .attrib { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #ddd5c8;
                    font-family: -apple-system, sans-serif; font-size: .8rem; color: #6d675e; }
          .attrib a { color: #8a6d3b; }
          @media (prefers-color-scheme: dark) {
            body { background: #1c1a17; color: #ece7dd; }
            mark { background: linear-gradient(transparent 55%, #7a5d13 55%); color: inherit; }
            .kicker { color: #c9a45c; } .attrib { color: #a39c90; border-top-color: #3a352e; } .attrib a { color: #c9a45c; }
            #pop { background: #faf8f4; color: #26221c; } #pop b { color: #8a6d3b; }
            .edited { text-decoration-color: #c9a45c; }
          }
        </style></head><body>
        <div class="kicker">\(label)</div><h1>\(title)</h1>
        \(body)
        <div class="attrib">\(attrib)</div>
        <div id="pop"></div>
        <script>
          const pop = document.getElementById('pop');
          const stats = \(statsJSON);
          function stem(w) { return w.trim().toLowerCase(); }
          function statFor(w) { const k = Object.keys(stats).find(x => stem(w).startsWith(x.slice(0, 6))); return k ? {word: k, id: stats[k][0], n: stats[k][1]} : null; }
          document.querySelectorAll('mark').forEach(m => {
            m.addEventListener('click', e => {
              e.stopPropagation();
              const s = statFor(m.textContent);
              let html = '<b>' + m.textContent.trim() + '</b> — ' + (m.dataset.def || '');
              if (s) {
                html += '<span class="meta">Seen ' + (s.n + 1) + ' time' + (s.n === 0 ? '' : 's') + '</span>';
                html += '<button onclick="event.stopPropagation(); this.disabled = true; this.textContent = \\'Marked retained\\'; try { window.webkit.messageHandlers.retain.postMessage(\\'' + s.word + '\\'); } catch (err) {}">Got it — mark retained</button>';
              }
              pop.innerHTML = html;
              pop.style.display = 'block';
              const r = m.getBoundingClientRect();
              pop.style.left = Math.min(r.left + window.scrollX, window.innerWidth - 300) + 'px';
              pop.style.top = (r.bottom + window.scrollY + 8) + 'px';
              try { window.webkit.messageHandlers.tap.postMessage(m.textContent.trim()); } catch (err) {}
            });
          });
          document.addEventListener('click', () => { pop.style.display = 'none'; });
        </script></body></html>
        """
    }
}
