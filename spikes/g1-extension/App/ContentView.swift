import SwiftUI

/// Stub main app: paste box (the universal fallback, story B4) + stub My Reads from the
/// app-group store + the shared debug log. `-autorun` launch argument runs a built-in
/// sample immediately (for scripted simulator smoke tests).
struct ContentView: View {
    @State private var text = ""
    @State private var showSheet = false
    @State private var reads: [Piece] = SharedStore.load()
    @State private var log = SharedStore.readLog()
    @State private var selected: Piece?

    var body: some View {
        NavigationStack {
            List {
                Section("RetAInize what you're reading") {
                    TextEditor(text: $text).frame(minHeight: 120).font(.body)
                    Button("Work the magic ✦") { showSheet = true }
                        .disabled(text.count < 200)
                    Text("\(text.count) chars (min 200)").font(.caption).foregroundStyle(.secondary)
                }
                Section("Your reads (app-group store: \(SharedStore.available ? "ok" : "MISSING"))") {
                    if reads.isEmpty { Text("Nothing yet.").foregroundStyle(.secondary) }
                    ForEach(reads) { p in
                        Button { selected = p } label: {
                            VStack(alignment: .leading) {
                                Text(p.title).font(.body)
                                Text("\(p.source) · \(p.markCount) words · \(p.latencyMs) ms").font(.caption).foregroundStyle(.secondary)
                            }
                        }
                    }
                }
                Section("Spike log") {
                    Text(log).font(.caption2.monospaced())
                }
            }
            .navigationTitle("RetAIn spike")
            .refreshable { reload() }
            .toolbar { Button("Reload") { reload() } }
        }
        .sheet(isPresented: $showSheet, onDismiss: reload) {
            SheetView(input: ExtensionInput(text: text, source: "app-paste")) { showSheet = false }
        }
        .sheet(item: $selected) { p in
            NavigationStack { PieceWebView(html: PieceHTML.page(for: p)).navigationTitle(p.title).navigationBarTitleDisplayMode(.inline) }
        }
        .onAppear {
            if CommandLine.arguments.contains("-autorun") { text = Sample.text; showSheet = true }
        }
    }
    private func reload() { reads = SharedStore.load(); log = SharedStore.readLog() }
}

enum Sample {
    static let text = """
    I've been at my company for about two years and things are mostly fine, but my manager has cancelled or moved our one-on-one six times in the last two months. Every time it's a last-minute message: sorry, something came up, let's do next week. Next week it happens again.

    I don't think she's doing it on purpose. She got two more direct reports in the spring and her calendar is a disaster. But the effect on me is real. I have a promotion case I want to build and I can't get twenty minutes to talk about it. Small decisions that need her sign-off are stalling.

    What I've tried: I sent a short agenda ahead of the last two meetings so she'd see there was something concrete. Didn't help. I asked if a different day would work better. She said Thursdays, then cancelled Thursday.

    How do I bring this up without sounding like I'm complaining about her workload, which she can't change?
    """
}
