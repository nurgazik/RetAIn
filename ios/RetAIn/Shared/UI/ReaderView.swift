import SwiftUI

/// The reader for a finished piece. Tapping a highlight records the tap ("didn't remember")
/// and opens the word's card in a bottom-half sheet (D48), with "Got it — mark retained"
/// (D12). Used by the share sheet and by My Reads.
struct ReaderView: View {
    let piece: Piece
    @State private var words: [Word] = []
    @State private var loaded = false
    @State private var shown: Word?

    var body: some View {
        Group {
            if loaded {
                PieceWebView(html: PieceHTML.page(title: piece.title ?? "", label: "Your read",
                                                  body: piece.bodyHtml ?? "", attrib: piece.attrib ?? "",
                                                  dek: piece.dek, byline: piece.byline, siteName: piece.siteName,
                                                  published: piece.published),
                             onTap: { text in
                                 EventQueue.shared.tap(pieceId: piece.id, word: text)  // D74: queued, dated when tapped
                                 shown = Self.match(text, in: words)
                             },
                             onSeen: { text in EventQueue.shared.shownInReader(pieceId: piece.id, word: text) })
                .ignoresSafeArea(edges: .bottom)
            } else {
                ProgressView()
            }
        }
        .sheet(item: $shown) { w in
            WordCardView(word: w, onStatus: { status in
                Task {
                    if status == "deleted" {  // D62: gone from the user's words; its highlight stays in this read
                        if (try? await RetAInClient.shared.deleteWord(w.id)) != nil { words.removeAll { $0.id == w.id } }
                    } else if let updated = try? await RetAInClient.shared.setWordStatus(w.id, status),
                              let i = words.firstIndex(where: { $0.id == w.id }) {
                        words[i].status = updated.status
                    }
                    shown = nil
                }
            }, onNote: { text in
                let saved = try await RetAInClient.shared.setNote(w.id, text)
                if let i = words.firstIndex(where: { $0.id == w.id }) { words[i].note = saved.note }  // next tap shows it
                return saved
            })
            .presentationDetents([.medium, .large])  // bottom half; drag up for long cards
            .presentationDragIndicator(.visible)
        }
        .task {
            words = (try? await RetAInClient.shared.words()) ?? []
            loaded = true
        }
        .task(id: piece.id) {  // D74: a read counts once the piece has been on screen for 10 s (an accidental open doesn't)
            try? await Task.sleep(for: .seconds(10))
            if !Task.isCancelled { EventQueue.shared.opened(pieceId: piece.id) }
        }
    }

    /// The printed form ("bolstered") → the user's word ("bolster"): exact first, then the
    /// engine's six-letter stem rule (generate.py annotate_marks).
    static func match(_ text: String, in words: [Word]) -> Word? {
        let t = text.lowercased()
        return words.first { $0.word == t } ?? words.first { t.hasPrefix(String($0.word.prefix(6))) }
    }
}
