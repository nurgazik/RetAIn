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
                 margin: 0; padding: 1.25rem 1.25rem 4rem 1.75rem; line-height: 1.65; -webkit-text-size-adjust: 100%; }
          .kicker { font-family: -apple-system, sans-serif; font-size: .75rem; letter-spacing: .12em;
                    text-transform: uppercase; color: #8a6d3b; margin-bottom: .5rem; }
          h1 { font-size: 1.5rem; line-height: 1.25; margin: 0 0 1.25rem; }
          p { margin: 0 0 1.1rem; font-size: 1.06rem; }
          mark { background: linear-gradient(transparent 55%, #ffe08a 55%); padding: 0 .1em; border-radius: 2px; }
          /* D40: no underlines — how a sentence was changed lives in the margin, per line */
          .edited { cursor: pointer; }
          .note { font-style: italic; cursor: pointer; }
          /* a bar is a tap zone filling the left margin; the visible stripe is its ::before */
          .bar { position: absolute; left: 0; width: 1.75rem; cursor: pointer; }
          .bar::before, .swatch::before { content: ""; position: absolute; top: 0; bottom: 0; width: 3px; border-radius: 1.5px; }
          .bar::before { left: .55rem; }
          .bar-note::before { width: 4px; }
          #hint { position: absolute; display: none; z-index: 11; max-width: 270px; padding: .6rem .75rem .6rem .7rem;
                  background: #fffdf8; color: #26221c; border: 1px solid #e3dbcc; border-radius: 10px;
                  box-shadow: 0 4px 14px rgba(0,0,0,.12); font-family: -apple-system, sans-serif; font-size: .82rem;
                  line-height: 1.4; gap: .6rem; align-items: stretch; }
          #hint .swatch { position: relative; flex: 0 0 4px; min-height: 2.2rem; }
          #hint .swatch::before { left: 0; }
          #hint b { display: block; font-size: .85rem; margin-bottom: .15rem; }
          .substitute mark { background: linear-gradient(transparent 55%, #b5e3a1 55%); }
          .rephrase mark   { background: linear-gradient(transparent 55%, #b3d4f5 55%); }
          .note mark       { background: linear-gradient(transparent 55%, #f8c9a0 55%); }
          .bar-substitute { --c: #4c9a3a; } .bar-rephrase { --c: #3d7fc4; } .bar-note { --c: #d9772b; }
          .bar-substitute::before { background: repeating-linear-gradient(to bottom, var(--c) 0 9px, transparent 9px 14px); }
          .bar-rephrase::before   { background: var(--c); }
          .bar-note::before       { background: repeating-linear-gradient(to bottom, var(--c) 0 4px, transparent 4px 8px); }
          #pop .orig { display: block; margin-top: .3rem; font-family: Georgia, serif; font-style: italic; }
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
            .substitute mark { background: linear-gradient(transparent 55%, #3d6b2f 55%); }
            .rephrase mark   { background: linear-gradient(transparent 55%, #2b5485 55%); }
            .note mark       { background: linear-gradient(transparent 55%, #8a4f22 55%); }
            .bar-substitute { --c: #7cc466; } .bar-rephrase { --c: #6aa6e6; } .bar-note { --c: #f0a060; }
            #hint { background: #2a2620; color: #ece7dd; border-color: #3f392f; box-shadow: 0 4px 14px rgba(0,0,0,.5); }
          }
        </style></head><body>
        <div class="kicker">\(label)</div><h1>\(title)</h1>
        \(body)
        <div class="attrib">\(attrib)</div>
        <div id="pop"></div>
        <div id="hint"></div>
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
              document.getElementById('hint').style.display = 'none';
              pop.innerHTML = html;
              pop.style.display = 'block';
              const r = m.getBoundingClientRect();
              pop.style.left = Math.min(r.left + window.scrollX, window.innerWidth - 300) + 'px';
              pop.style.top = (r.bottom + window.scrollY + 8) + 'px';
              try { window.webkit.messageHandlers.tap.postMessage(m.textContent.trim()); } catch (err) {}
            });
          });
          function showAt(html, x, y) {
            document.getElementById('hint').style.display = 'none';
            pop.innerHTML = html;
            pop.style.display = 'block';
            pop.style.left = Math.min(x, window.innerWidth - 300) + 'px';
            pop.style.top = (y + 8) + 'px';
          }
          // D40: tapping a changed sentence (not its word) reveals the source sentence.
          document.querySelectorAll('.edited[data-orig]').forEach(sp => {
            sp.addEventListener('click', e => {
              e.stopPropagation();
              const label = sp.dataset.tier === 'substitute' ? 'Word substituted' : 'Sentence rephrased';
              showAt('<b>' + label + '</b> — original:<span class="orig"></span>', e.pageX, e.pageY + 12);
              pop.querySelector('.orig').textContent = sp.dataset.orig;
            });
          });
          // D40: a note has no original; tapping it (not its word) says where it came from.
          document.querySelectorAll('.note').forEach(n => {
            n.addEventListener('click', e => {
              e.stopPropagation();
              showAt('<b>Added by RetAIn</b> — general context, not from the article.', e.pageX, e.pageY + 12);
            });
          });
          const hint = document.getElementById('hint');
          const HINTS = {
            substitute: ['Word substituted', 'One word in this sentence was swapped for one of yours. Tap the sentence to see the original.'],
            rephrase: ['Sentence rephrased', 'Reworded to carry one of your words; the facts are the source’s. Tap the sentence to see the original.'],
            note: ['Note from RetAIn', 'General background added to carry one of your words — not from the article.']
          };
          function showHint(kind, top) {
            pop.style.display = 'none';
            hint.innerHTML = '<span class="swatch bar-' + kind + '"></span><div><b class="h-title"></b><span class="h-text"></span></div>';
            hint.querySelector('.h-title').textContent = HINTS[kind][0];
            hint.querySelector('.h-text').textContent = HINTS[kind][1];
            hint.style.left = '1.9rem'; hint.style.top = top + 'px';
            hint.style.display = 'flex';
          }
          document.addEventListener('click', () => { pop.style.display = 'none'; hint.style.display = 'none'; });
          // D40 margin bars: one per visual line of every changed sentence and note, styled
          // by tier. When two share a line, the stronger change wins (note > rephrase > substitute).
          function drawBars() {
            document.querySelectorAll('.bar').forEach(b => b.remove());
            const rank = {substitute: 1, rephrase: 2, note: 3}, lines = [];
            document.querySelectorAll('.edited, .note').forEach(el => {
              const kind = el.classList.contains('note') ? 'note' : el.classList.contains('rephrase') ? 'rephrase' : 'substitute';
              const lh = parseFloat(getComputedStyle(el).lineHeight) || 0;
              for (const r of el.getClientRects()) {
                if (r.width < 1) continue;
                const h = Math.max(r.height, lh), top = r.top + window.scrollY - (h - r.height) / 2;
                const same = lines.find(l => Math.abs(l.top - top) < h / 2);
                if (!same) lines.push({top, h, kind});
                else if (rank[kind] > rank[same.kind]) same.kind = kind;
              }
            });
            // consecutive lines of the same kind become one bar, so dashes and dots read as a line
            lines.sort((a, b) => a.top - b.top);
            const runs = [];
            lines.forEach(l => {
              const last = runs[runs.length - 1];
              if (last && last.kind === l.kind && l.top <= last.top + last.h + 2) last.h = l.top + l.h - last.top;
              else runs.push({...l});
            });
            runs.forEach(l => {
              const b = document.createElement('div');
              b.className = 'bar bar-' + l.kind;
              b.style.top = l.top + 'px'; b.style.height = l.h + 'px';
              b.addEventListener('click', e => { e.stopPropagation(); showHint(l.kind, l.top); });
              document.body.appendChild(b);
            });
          }
          drawBars();
          window.addEventListener('resize', drawBars);
          if (document.fonts) document.fonts.ready.then(drawBars);
        </script></body></html>
        """
    }
}
