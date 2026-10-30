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
    @State private var query = ""      // search (App/WordSearch.swift)
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack(path: $path) {
            List {
                if searching { searchResults } else { allWords }
                if let error { Text(error).foregroundStyle(.red).font(.caption) }
            }
            .searchable(text: $query, placement: .navigationBarDrawer(displayMode: .always),
                        prompt: "Search words, meanings, notes")
            .autocorrectionDisabled().textInputAutocapitalization(.never)
            .navigationTitle("Words")
            .navigationDestination(for: Word.self) { w in
                WordCardView(word: w, onStatus: { status in Task { await set(w, status); path.removeAll() } },
                             onNote: { text in let saved = try await RetAInClient.shared.setNote(w.id, text); await load(); return saved })
            }
            .onChange(of: openWordId, initial: true) { _, _ in openPending() }
            .onChange(of: words) { _, _ in openPending() }
            .refreshable { await load() }
            .task { await load() }
            .onChange(of: scenePhase) { _, phase in if phase == .active { Task { await load() } } }
        }
    }

    private var searching: Bool { !WordSearch.fold(query).isEmpty }

    @ViewBuilder private var allWords: some View {
        Section {
            HStack {
                TextField("Add a word", text: $newWord).textInputAutocapitalization(.never).autocorrectionDisabled()
                    .onSubmit { Task { await add(newWord) } }
                Button("Add") { Task { await add(newWord) } }.disabled(newWord.trimmingCharacters(in: .whitespaces).isEmpty || busy)
            }
        }
        ForEach(groups, id: \.0) { status, list in
            Section("\(status) · \(list.count)") {
                ForEach(list) { w in row(w, nil) }
            }
        }
    }

    /// Ranked hits (exact, starts with, a form of it, contains, your note, a meaning, a near-miss
    /// spelling); "Add" when the query isn't a saved word, so searching first also avoids duplicates.
    @ViewBuilder private var searchResults: some View {
        let hits = WordSearch.results(words, query)
        let typed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        if hits.isEmpty {
            addRow(typed, hits)
            ContentUnavailableView.search(text: typed)
        } else {  // results first: a misspelling shouldn't sit above the word it probably means
            Section("\(hits.count) result\(hits.count == 1 ? "" : "s")") {
                ForEach(hits) { h in row(h.word, h) }
            }
            addRow(typed, hits)
        }
    }

    /// No "Add" when the word is already saved, or saved in its dictionary form (the server would fold
    /// "bolstered" into "bolster" anyway, D58).
    @ViewBuilder private func addRow(_ typed: String, _ hits: [WordSearch.Hit]) -> some View {
        if !WordSearch.hasExact(words, typed), !hits.contains(where: { $0.tier == 2 }), !typed.contains(" ") {
            Section {
                Button { Task { await add(typed) } } label: {
                    HStack { Label("Add “\(typed.lowercased())”", systemImage: "plus.circle"); if busy { Spacer(); ProgressView() } }
                }
                .disabled(busy).accessibilityIdentifier("search-add")
            }
        }
    }

    private func row(_ w: Word, _ hit: WordSearch.Hit?) -> some View {
        NavigationLink(value: w) {
            VStack(alignment: .leading) {
                HStack {
                    Text(highlighted(w.word)).font(.body.weight(.medium))
                    if let r = w.rarity { Text(r.dots).font(.caption2).foregroundStyle(.secondary).accessibilityLabel(r.label) }
                    if let n = w.servings, n > 0 { Text("· \(n)").foregroundStyle(.secondary).font(.caption) }
                    if w.isUnverified { Text("Unverified").font(.caption2).foregroundStyle(.orange) }
                    if w.note?.isEmpty == false { Image(systemName: "note.text").font(.caption).foregroundStyle(.secondary).accessibilityLabel("Has a note") }
                    if hit != nil, w.status == "retained" { Text("retained").font(.caption2).foregroundStyle(.green) }
                }
                switch hit?.field {
                case .note?: Text("Your note: " + highlighted(hit?.snippet ?? "")).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                case .meaning?: Text(highlighted(hit?.snippet ?? "")).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                default: Text(w.firstDefinition).font(.caption).foregroundStyle(.secondary).lineLimit(1)
                }
            }
        }
        .swipeActions(edge: .trailing) {
            Button("Delete", role: .destructive) { Task { await set(w, "deleted") } }
            if w.status != "retained" { Button("Retained") { Task { await set(w, "retained") } }.tint(.green) }
            if w.status != "learning" { Button("Learning") { Task { await set(w, "learning") } }.tint(.orange) }
        }
    }

    /// The search terms in bold, ignoring case and accents (the same rules as matching).
    private func highlighted(_ text: String) -> AttributedString {
        var out = AttributedString(text)
        guard searching else { return out }
        for term in WordSearch.fold(query).split(separator: " ") {
            var from = out.startIndex
            while let r = out[from...].range(of: String(term), options: [.caseInsensitive, .diacriticInsensitive]) {
                out[r].inlinePresentationIntent = .stronglyEmphasized
                from = r.upperBound
            }
        }
        return out
    }

    private var groups: [(String, [Word])] {
        ["learning", "retained"].compactMap { s in  // deleted words never come back from the server (D62)
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
    private func add(_ text: String) async {
        let w = text.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !w.isEmpty else { return }
        busy = true; defer { busy = false }
        do { _ = try await RetAInClient.shared.addWord(w); newWord = ""; await load() } catch { self.error = error.localizedDescription }
    }
    private func set(_ w: Word, _ status: String) async {
        do {
            if status == "deleted" { _ = try await RetAInClient.shared.deleteWord(w.id) }
            else { _ = try await RetAInClient.shared.setWordStatus(w.id, status) }
            await load()
        } catch { self.error = error.localizedDescription }
    }
}
