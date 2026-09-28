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
                                 Task { try? await RetAInClient.shared.tap(pieceId: piece.id, word: text) }
                                 shown = Self.match(text, in: words)
                             })
                .ignoresSafeArea(edges: .bottom)
            } else {
                ProgressView()
            }
        }
        .sheet(item: $shown) { w in
            WordCardView(word: w) { status in
                Task {
                    if let updated = try? await RetAInClient.shared.setWordStatus(w.id, status),
                       let i = words.firstIndex(where: { $0.id == w.id }) {
                        words[i].status = updated.status
                    }
                    shown = nil
                }
            }
            .presentationDetents([.medium, .large])  // bottom half; drag up for long cards
            .presentationDragIndicator(.visible)
        }
        .task {
            words = (try? await RetAInClient.shared.words()) ?? []
            loaded = true
        }
    }

    /// The printed form ("bolstered") → the user's word ("bolster"): exact first, then the
    /// engine's six-letter stem rule (generate.py annotate_marks).
    static func match(_ text: String, in words: [Word]) -> Word? {
        let t = text.lowercased()
        return words.first { $0.word == t } ?? words.first { t.hasPrefix(String($0.word.prefix(6))) }
    }
}
