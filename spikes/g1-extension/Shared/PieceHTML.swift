import Foundation

/// Same reader CSS + tap-to-reveal JS as src/generate.py, so the sheet reads like the PoC page.
enum PieceHTML {
    static func page(for p: Piece) -> String {
        """
        <!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body { font-family: Georgia, 'Times New Roman', serif; background: #faf8f4; color: #26221c;
                 margin: 0; padding: 1.25rem 1.25rem 4rem; line-height: 1.65; }
          .kicker { font-family: -apple-system, sans-serif; font-size: .75rem; letter-spacing: .12em;
                    text-transform: uppercase; color: #8a6d3b; margin-bottom: .5rem; }
          h1 { font-size: 1.5rem; line-height: 1.25; margin: 0 0 1.25rem; }
          p { margin: 0 0 1.1rem; font-size: 1.06rem; }
          mark { background: linear-gradient(transparent 55%, #ffe08a 55%); padding: 0 .1em; border-radius: 2px; }
          #pop { position: absolute; display: none; z-index: 10; max-width: 280px; padding: .6rem .8rem;
                 background: #26221c; color: #faf8f4; border-radius: 8px; font-family: -apple-system, sans-serif;
                 font-size: .85rem; line-height: 1.45; }
          #pop b { color: #ffd76e; }
          .attrib { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #ddd5c8;
                    font-family: -apple-system, sans-serif; font-size: .8rem; color: #6d675e; }
        </style></head><body>
        <div class="kicker">\(p.label)</div><h1>\(p.title)</h1>
        \(p.body)
        <div class="attrib">\(p.attrib)</div>
        <div id="pop"></div>
        <script>
          const pop = document.getElementById('pop');
          document.querySelectorAll('mark').forEach(m => {
            m.addEventListener('click', e => {
              e.stopPropagation();
              pop.innerHTML = '<b>' + m.textContent.trim() + '</b> — ' + (m.dataset.def || '');
              pop.style.display = 'block';
              const r = m.getBoundingClientRect();
              pop.style.left = Math.min(r.left + window.scrollX, window.innerWidth - 300) + 'px';
              pop.style.top = (r.bottom + window.scrollY + 8) + 'px';
            });
          });
          document.addEventListener('click', () => { pop.style.display = 'none'; });
        </script></body></html>
        """
    }
}
