import SwiftUI

struct WordsView: View {
    @State private var words: [Word] = []
    @State private var newWord = ""
    @State private var error: String?
    @State private var busy = false

    var body: some View {
        NavigationStack {
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
                            NavigationLink { WordCardView(word: w) } label: {
                                VStack(alignment: .leading) {
                                    HStack { Text(w.word).font(.body.weight(.medium)); if let n = w.servings, n > 0 { Text("· \(n)").foregroundStyle(.secondary).font(.caption) } }
                                    Text(w.definition).font(.caption).foregroundStyle(.secondary).lineLimit(1)
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
            .refreshable { await load() }
            .task { await load() }
        }
    }

    private var groups: [(String, [Word])] {
        ["learning", "retained", "archived"].compactMap { s in
            let l = words.filter { $0.status == s }; return l.isEmpty ? nil : (s, l)
        }
    }
    private func load() async {
        do { words = try await RetAInClient.shared.words(); error = nil } catch { self.error = error.localizedDescription }
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
