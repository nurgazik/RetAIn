import SwiftUI

/// The reader for a finished piece: highlights, tap-to-reveal with "Seen N times" and a
/// "Got it" that marks the word retained (D12). Used by the sheet and by My Reads.
struct ReaderView: View {
    let piece: Piece
    @State private var stats: [String: [Int]] = [:]
    @State private var loaded = false

    var body: some View {
        Group {
            if loaded {
                PieceWebView(html: PieceHTML.page(title: piece.title ?? "", label: "Your read",
                                                  body: piece.bodyHtml ?? "", attrib: piece.attrib ?? "", stats: stats),
                             onTap: { word in Task { try? await RetAInClient.shared.tap(pieceId: piece.id, word: word) } },
                             onRetain: { word in
                                 guard let id = stats[word]?.first else { return }
                                 Task { _ = try? await RetAInClient.shared.setWordStatus(id, "retained") }
                             })
                .ignoresSafeArea(edges: .bottom)
            } else {
                ProgressView()
            }
        }
        .task {
            if let words = try? await RetAInClient.shared.words() {
                var m: [String: [Int]] = [:]
                for w in words { m[w.word.lowercased()] = [w.id, w.servings ?? 0] }
                stats = m
            }
            loaded = true
        }
    }
}
