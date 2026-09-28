import SwiftUI
import WidgetKit

struct WordsView: View {
    /// Set by a widget tap (retain://word/<id>): open that word's card once the list is loaded.
    @Binding var openWordId: Int?
    @State private var words: [Word] = []
    @State private var path: [Word] = []
    @State private var newWord = ""
    @State private var error: String?
    @State private var busy = false
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack(path: $path) {
            List {
                Section {
                    HStack {
                        TextField("Add a word", text: $newWord).textInputAutocapitalization(.never).autocorrectionDisabled()
                            .onSubmit { Task { await add() } }
                        Button("Add") { Task { await add() } }.disabled(newWord.trimmingCharacters(in: .whitespaces).isEmpty || busy)
                    }
                }
                ForEach(groups, id: \.0) { status, list in
                    Section("\(status) · \(list.count)") {
                        ForEach(list) { w in
                            NavigationLink(value: w) {
                                VStack(alignment: .leading) {
                                    HStack {
                                        Text(w.word).font(.body.weight(.medium))
                                        if let n = w.servings, n > 0 { Text("· \(n)").foregroundStyle(.secondary).font(.caption) }
                                        if w.isUnverified { Text("Unverified").font(.caption2).foregroundStyle(.orange) }
                                    }
                                    Text(w.firstDefinition).font(.caption).foregroundStyle(.secondary).lineLimit(1)
                                }
                            }
                            .swipeActions(edge: .trailing) {
                                if w.status != "retained" { Button("Retained") { Task { await set(w, "retained") } }.tint(.green) }
                                if w.status != "learning" { Button("Learning") { Task { await set(w, "learning") } }.tint(.orange) }
                                if w.status != "archived" { Button("Archive") { Task { await set(w, "archived") } }.tint(.gray) }
                            }
                        }
                    }
                }
                if let error { Text(error).foregroundStyle(.red).font(.caption) }
            }
            .navigationTitle("Words")
            .navigationDestination(for: Word.self) { w in
                WordCardView(word: w) { status in Task { await set(w, status); path.removeAll() } }
            }
            .onChange(of: openWordId, initial: true) { _, _ in openPending() }
            .onChange(of: words) { _, _ in openPending() }
            .refreshable { await load() }
            .task { await load() }
            .onChange(of: scenePhase) { _, phase in if phase == .active { Task { await load() } } }
        }
    }

    private var groups: [(String, [Word])] {
        ["learning", "retained", "archived"].compactMap { s in
            let l = words.filter { $0.status == s }; return l.isEmpty ? nil : (s, l)
        }
    }
    private func openPending() {
        guard let id = openWordId, let w = words.first(where: { $0.id == id }) else { return }
        path = [w]; openWordId = nil
    }
    private func load() async {
        do {
            words = try await RetAInClient.shared.words(); error = nil
            WordsStore.replaceAll(words); WidgetCenter.shared.reloadAllTimelines()
        } catch { self.error = error.localizedDescription }
    }
    private func add() async {
        let w = newWord.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !w.isEmpty else { return }
        busy = true; defer { busy = false }
        do { _ = try await RetAInClient.shared.addWord(w); newWord = ""; await load() } catch { self.error = error.localizedDescription }
    }
    private func set(_ w: Word, _ status: String) async {
        do { _ = try await RetAInClient.shared.setWordStatus(w.id, status); await load() } catch { self.error = error.localizedDescription }
    }
}
