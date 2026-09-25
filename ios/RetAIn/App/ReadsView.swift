import SwiftUI

struct ReadsView: View {
    @State private var pieces: [PieceSummary] = []
    @State private var selected: Piece?
    @State private var error: String?

    var body: some View {
        NavigationStack {
            List {
                if pieces.isEmpty { Text("Nothing yet. Share some text to RetAIn, or paste it in the RetAInize tab.").foregroundStyle(.secondary) }
                ForEach(pieces) { p in
                    Button { Task { await open(p) } } label: {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(p.title ?? "Untitled").font(.body)
                            Text("\(String(p.createdAt.prefix(10))) · \(p.wordsUsed.count) word\(p.wordsUsed.count == 1 ? "" : "s")\(p.wordsUsed.isEmpty ? "" : ": " + p.wordsUsed.joined(separator: ", "))")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                }
                if let error { Text(error).foregroundStyle(.red).font(.caption) }
            }
            .navigationTitle("My Reads")
            .refreshable { await load() }
            .task { await load() }
            .sheet(item: $selected) { p in
                NavigationStack {
                    PieceWebView(html: PieceHTML.page(title: p.title ?? "", label: "Your read", body: p.bodyHtml ?? "", attrib: p.attrib ?? "")) { word in
                        Task { try? await RetAInClient.shared.tap(pieceId: p.id, word: word) }
                    }
                    .ignoresSafeArea(edges: .bottom)
                    .navigationTitle(p.title ?? "").navigationBarTitleDisplayMode(.inline)
                    .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Done") { selected = nil } } }
                }
            }
        }
    }
    private func load() async {
        do { pieces = try await RetAInClient.shared.pieces().filter { $0.status == "done" }; error = nil }
        catch { self.error = error.localizedDescription }
    }
    private func open(_ s: PieceSummary) async {
        if let cached = ReadsStore.load().first(where: { $0.id == s.id }) { selected = cached; return }
        do { let p = try await RetAInClient.shared.piece(s.id); ReadsStore.save(p); selected = p }
        catch { self.error = error.localizedDescription }
    }
}
