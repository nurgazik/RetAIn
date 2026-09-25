import SwiftUI

/// The product moment (PRD §8): "working the magic" phases → the piece with highlights →
/// tap-to-reveal, with each tap sent to the ledger. Used by the app's paste flow and by
/// both extensions.
struct SheetView: View {
    let text: String
    var title: String? = nil
    var url: String? = nil
    let source: String
    let onDone: () -> Void

    enum Phase { case sending, working(String), done(Piece), failed(String) }
    @State private var phase: Phase = .sending
    @State private var elapsed = 0
    private let tick = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    var body: some View {
        NavigationStack {
            Group {
                switch phase {
                case .sending, .working:
                    VStack(spacing: 14) {
                        Image(systemName: "sparkles").font(.system(size: 40)).foregroundStyle(.orange).symbolEffect(.pulse)
                        Text("Working the magic — rewriting this just for you…").font(.callout).multilineTextAlignment(.center)
                        Text(phaseLabel).font(.caption).foregroundStyle(.secondary)
                        Text("\(elapsed)s").font(.caption2).foregroundStyle(.tertiary)
                    }.padding()
                case .done(let p):
                    PieceWebView(html: PieceHTML.page(title: p.title ?? "", label: "Your read",
                                                      body: p.bodyHtml ?? "", attrib: p.attrib ?? "")) { word in
                        Task { try? await RetAInClient.shared.tap(pieceId: p.id, word: word) }
                    }
                    .ignoresSafeArea(edges: .bottom)
                case .failed(let msg):
                    VStack(spacing: 12) {
                        Text("Couldn't transform this.").font(.headline)
                        Text(msg).font(.callout).foregroundStyle(.secondary).multilineTextAlignment(.center)
                    }.padding()
                }
            }
            .navigationTitle("RetAIn").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Done") { onDone() } } }
        }
        .onReceive(tick) { _ in elapsed += 1 }
        .task { await run() }
    }

    private var phaseLabel: String {
        switch phase {
        case .sending: return "sending"
        case .working(let p):
            return ["queued": "queued", "generating": "placing your words", "checking": "checking every word",
                    "regenerating": "fixing a word that didn't fit", "repairing": "polishing"][p] ?? p
        default: return ""
        }
    }

    private func run() async {
        do {
            let accepted = try await RetAInClient.shared.transform(text: text, title: title, url: url, source: source)
            for try await ev in try RetAInClient.shared.events(pieceId: accepted.pieceId) {
                switch ev {
                case .phase(let p): phase = .working(p)
                case .piece(let piece):
                    ReadsStore.save(piece)
                    phase = .done(piece)
                    return
                case .error(let e):
                    phase = .failed(e)
                    return
                }
            }
            if case .working = phase { phase = .failed("The stream ended before the piece arrived.") }
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}
