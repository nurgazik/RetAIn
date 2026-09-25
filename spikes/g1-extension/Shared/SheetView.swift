import SwiftUI
import WebKit

/// The product moment, shared by the app's paste flow and both extensions:
/// "working the magic" → the piece with highlights → Done.
struct SheetView: View {
    let input: ExtensionInput
    var launchMs: Int = 0
    let onDone: () -> Void

    enum Phase { case loading, done(Piece), failed(String) }
    @State private var phase: Phase = .loading
    @State private var elapsed = 0
    @State private var memAtStart = residentMemoryMB()
    @State private var memPeak = residentMemoryMB()
    @State private var showDebug = false
    private let tick = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    var body: some View {
        NavigationStack {
            Group {
                switch phase {
                case .loading:
                    VStack(spacing: 14) {
                        Image(systemName: "sparkles").font(.system(size: 40)).foregroundStyle(.orange)
                            .symbolEffect(.pulse)
                        Text("Working the magic — rewriting this just for you…").font(.callout)
                        Text("\(elapsed)s").font(.caption).foregroundStyle(.secondary)
                    }.padding()
                case .done(let p):
                    PieceWebView(html: PieceHTML.page(for: p))
                case .failed(let msg):
                    VStack(spacing: 12) {
                        Text("Couldn't transform this.").font(.headline)
                        Text(msg).font(.callout).foregroundStyle(.secondary).multilineTextAlignment(.center)
                        Text(input.summary).font(.caption2.monospaced()).foregroundStyle(.secondary)
                    }.padding()
                }
            }
            .safeAreaInset(edge: .bottom) { footer }
            .navigationTitle("RetAIn").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Done") { onDone() } }
                ToolbarItem(placement: .primaryAction) { Button(showDebug ? "Hide" : "Debug") { showDebug.toggle() } }
            }
        }
        .onReceive(tick) { _ in
            elapsed += 1
            memPeak = max(memPeak, residentMemoryMB())
        }
        .task { await run() }
    }

    private var footer: some View {
        VStack(alignment: .leading, spacing: 4) {
            if case .done(let p) = phase {
                Text("\(p.markCount) words · \(p.wordCount) words long · \(p.latencyMs) ms · launch \(launchMs) ms")
            }
            Text(String(format: "memory %.0f MB now · %.0f MB peak · %.0f MB at open · group %@",
                        residentMemoryMB(), memPeak, memAtStart, SharedStore.available ? "ok" : "MISSING"))
            if showDebug { Text(input.summary) }
        }
        .font(.caption2.monospaced()).foregroundStyle(.secondary)
        .frame(maxWidth: .infinity, alignment: .leading).padding(8).background(.thinMaterial)
    }

    private func run() async {
        SharedStore.log("sheet open source=\(input.source) launch=\(launchMs)ms mem=\(Int(memAtStart))MB\n\(input.summary)")
        guard let text = input.effectiveText else {
            phase = .failed("Nothing readable arrived (need ≥200 characters of text). Select some text and share the selection.")
            SharedStore.log("no usable text")
            return
        }
        do {
            var p = try await TransformClient.transform(text: text, title: input.title, url: input.url, source: input.source)
            p.source = input.source
            SharedStore.save(p)
            SharedStore.log("done id=\(p.id) marks=\(p.markCount) words=\(p.wordCount) latency=\(p.latencyMs)ms memPeak=\(Int(memPeak))MB")
            phase = .done(p)
        } catch {
            SharedStore.log("failed: \(error.localizedDescription)")
            phase = .failed(error.localizedDescription)
        }
    }
}

struct PieceWebView: UIViewRepresentable {
    let html: String
    func makeUIView(context: Context) -> WKWebView {
        let w = WKWebView()
        w.isOpaque = false
        w.loadHTMLString(html, baseURL: nil)
        return w
    }
    func updateUIView(_ uiView: WKWebView, context: Context) {}
}
